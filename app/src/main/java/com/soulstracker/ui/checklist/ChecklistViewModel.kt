package com.soulstracker.ui.checklist

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.soulstracker.data.Checklist
import com.soulstracker.data.ChecklistRepository
import com.soulstracker.data.Entry
import com.soulstracker.data.ProgressStore
import com.soulstracker.data.Sheet
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.filterNotNull
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.Locale

enum class StatusFilter(val label: String) { All("All"), Remaining("Remaining"), Done("Done") }

sealed interface ChecklistRow {
    val key: String

    data class Header(val entry: Entry, val done: Int, val total: Int, val collapsed: Boolean) : ChecklistRow {
        override val key get() = "h-${entry.id}"
    }

    data class Task(val entry: Entry, val done: Boolean) : ChecklistRow {
        override val key get() = entry.id
    }
}

data class SheetSummary(val title: String, val done: Int, val total: Int)

data class ChecklistUiState(
    val loading: Boolean = true,
    val title: String = "",
    val tips: List<String> = emptyList(),
    val sheets: List<SheetSummary> = emptyList(),
    val selectedSheet: Int = 0,
    val query: String = "",
    val status: StatusFilter = StatusFilter.All,
    val category: String? = null,
    val categories: List<String> = emptyList(),
    val rows: List<ChecklistRow> = emptyList(),
    val completed: Set<String> = emptySet(),
)

private data class Inputs(
    val sheet: Int = 0,
    val query: String = "",
    val status: StatusFilter = StatusFilter.All,
    val category: String? = null,
    val collapsed: Set<String> = emptySet(),
)

private class Section(val header: Entry, val tasks: List<Entry>)

fun Sheet.tasks(): List<Entry> = entries.filter { !it.section }

fun percent(done: Int, total: Int): String =
    if (total == 0) "0%" else String.format(Locale.US, "%.1f%%", done * 100f / total)

private fun Sheet.sections(): List<Section> {
    val out = mutableListOf<Section>()
    var header = Entry(id = "$id-start", step = 0, item = "Start", section = true)
    var tasks = mutableListOf<Entry>()
    for (e in entries) {
        if (e.section) {
            if (tasks.isNotEmpty()) out += Section(header, tasks)
            header = e
            tasks = mutableListOf()
        } else {
            tasks += e
        }
    }
    if (tasks.isNotEmpty()) out += Section(header, tasks)
    return out
}

class ChecklistViewModel(
    private val gameId: String,
    private val repository: ChecklistRepository,
    private val progress: ProgressStore,
) : ViewModel() {

    private val checklist = MutableStateFlow<Checklist?>(null)
    private val sections = MutableStateFlow<List<List<Section>>>(emptyList())
    private val inputs = MutableStateFlow(Inputs())

    init {
        viewModelScope.launch {
            val loaded = repository.load(gameId)
            sections.value = loaded.sheets.map { it.sections() }
            checklist.value = loaded
        }
    }

    val state: StateFlow<ChecklistUiState> = combine(
        checklist.filterNotNull(),
        progress.completed(gameId),
        inputs,
    ) { list, done, input -> build(list, sections.value, done, input) }
        .flowOn(Dispatchers.Default)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), ChecklistUiState())

    private fun build(list: Checklist, allSections: List<List<Section>>, done: Set<String>, input: Inputs): ChecklistUiState {
        val sheet = list.sheets[input.sheet]
        val query = input.query.trim().lowercase()
        val filtering = query.isNotEmpty() || input.status != StatusFilter.All || input.category != null

        val rows = mutableListOf<ChecklistRow>()
        for (section in allSections[input.sheet]) {
            val matches = section.tasks.filter { e ->
                val isDone = e.id in done
                (input.status == StatusFilter.All || (input.status == StatusFilter.Done) == isDone) &&
                    (input.category == null || e.category.equals(input.category, ignoreCase = true)) &&
                    (query.isEmpty() || e.item.lowercase().contains(query) || e.location.lowercase().contains(query) ||
                        e.notes.lowercase().contains(query))
            }
            if (filtering && matches.isEmpty()) continue
            // While filtering, show every match even inside collapsed sections.
            val collapsed = !filtering && section.header.id in input.collapsed
            rows += ChecklistRow.Header(section.header, section.tasks.count { it.id in done }, section.tasks.size, collapsed)
            if (!collapsed) matches.mapTo(rows) { ChecklistRow.Task(it, it.id in done) }
        }

        return ChecklistUiState(
            loading = false,
            title = list.title,
            tips = list.tips,
            sheets = list.sheets.map { s -> s.tasks().let { t -> SheetSummary(s.title, t.count { it.id in done }, t.size) } },
            selectedSheet = input.sheet,
            query = input.query,
            status = input.status,
            category = input.category,
            categories = sheet.tasks().map { it.category.trim() }.filter { it.isNotEmpty() }
                .distinctBy { it.lowercase() }.sorted(),
            rows = rows,
            completed = done,
        )
    }

    fun selectSheet(index: Int) = inputs.update { it.copy(sheet = index, category = null) }
    fun setQuery(query: String) = inputs.update { it.copy(query = query) }
    fun setStatus(status: StatusFilter) = inputs.update { it.copy(status = status) }
    fun setCategory(category: String?) = inputs.update { it.copy(category = category) }

    fun toggleSection(headerId: String) = inputs.update {
        it.copy(collapsed = if (headerId in it.collapsed) it.collapsed - headerId else it.collapsed + headerId)
    }

    fun setAllCollapsed(collapsed: Boolean) = inputs.update { input ->
        input.copy(collapsed = if (collapsed) sections.value[input.sheet].map { it.header.id }.toSet() else emptySet())
    }

    fun setDone(entry: Entry, done: Boolean) {
        viewModelScope.launch { progress.setDone(gameId, entry.id, done) }
    }

    fun resetSheet() {
        val sheet = checklist.value?.sheets?.get(inputs.value.sheet) ?: return
        viewModelScope.launch { progress.reset(gameId, sheet.entries.map { it.id }.toSet()) }
    }

    fun entry(id: String): Entry? = checklist.value?.sheets?.firstNotNullOfOrNull { s -> s.entries.find { it.id == id } }
}
