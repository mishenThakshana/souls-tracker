package com.soulstracker.ui.checklist

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.asPaddingValues
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.FilterList
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.Place
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Badge
import androidx.compose.material3.BadgedBox
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.PrimaryTabRow
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.nestedscroll.NestedScrollConnection
import androidx.compose.ui.input.nestedscroll.NestedScrollSource
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.layout.layout
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.soulstracker.SoulsTrackerApp
import com.soulstracker.ui.theme.Ember
import kotlin.math.roundToInt

@OptIn(ExperimentalMaterial3Api::class, ExperimentalFoundationApi::class)
@Composable
fun ChecklistScreen(app: SoulsTrackerApp, gameId: String, onBack: () -> Unit) {
    val vm: ChecklistViewModel = viewModel(
        key = gameId,
        factory = viewModelFactory { initializer { ChecklistViewModel(gameId, app.repository, app.progress) } },
    )
    val state by vm.state.collectAsStateWithLifecycle()
    var infoEntryId by rememberSaveable { mutableStateOf<String?>(null) }
    var showTips by rememberSaveable { mutableStateOf(false) }
    var confirmReset by rememberSaveable { mutableStateOf(false) }
    var menuOpen by remember { mutableStateOf(false) }
    var showFilters by rememberSaveable { mutableStateOf(false) }

    val listState = rememberLazyListState()

    // Header (app bar, tabs, progress, search, filters) slides away while scrolling down
    // and slides back in while scrolling up.
    var headerHeight by remember { mutableIntStateOf(0) }
    var headerOffset by remember { mutableFloatStateOf(0f) }
    val headerScroll = remember {
        object : NestedScrollConnection {
            override fun onPreScroll(available: Offset, source: NestedScrollSource): Offset {
                val next = (headerOffset + available.y).coerceIn(-headerHeight.toFloat(), 0f)
                val consumed = next - headerOffset
                headerOffset = next
                return Offset(0f, consumed)
            }
        }
    }
    LaunchedEffect(state.selectedSheet) {
        listState.scrollToItem(0)
        headerOffset = 0f
    }

    Column(
        Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .statusBarsPadding()
            .nestedScroll(headerScroll),
    ) {
        Column(
            Modifier
                .clipToBounds()
                .layout { measurable, constraints ->
                    val placeable = measurable.measure(constraints.copy(maxHeight = Constraints.Infinity))
                    headerHeight = placeable.height
                    val offset = headerOffset.roundToInt().coerceIn(-placeable.height, 0)
                    layout(placeable.width, placeable.height + offset) { placeable.place(0, offset) }
                },
        ) {
            TopAppBar(
                title = { Text(state.title.ifEmpty { "Checklist" }) },
                navigationIcon = {
                    IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back") }
                },
                actions = {
                    if (state.tips.isNotEmpty()) {
                        IconButton(onClick = { showTips = true }) { Icon(Icons.Filled.Lightbulb, contentDescription = "Guide tips") }
                    }
                    Box {
                        IconButton(onClick = { menuOpen = true }) { Icon(Icons.Filled.MoreVert, contentDescription = "More") }
                        DropdownMenu(expanded = menuOpen, onDismissRequest = { menuOpen = false }) {
                            DropdownMenuItem(text = { Text("Collapse all sections") }, onClick = { menuOpen = false; vm.setAllCollapsed(true) })
                            DropdownMenuItem(text = { Text("Expand all sections") }, onClick = { menuOpen = false; vm.setAllCollapsed(false) })
                            DropdownMenuItem(
                                text = { Text("Reset this tab's progress", color = MaterialTheme.colorScheme.error) },
                                onClick = { menuOpen = false; confirmReset = true },
                            )
                        }
                    }
                },
                windowInsets = WindowInsets(0),
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            )
            if (!state.loading) {
                SheetTabs(state, onSelect = vm::selectSheet)
                ProgressSummary(state)
                SearchRow(state, onQuery = vm::setQuery, onOpenFilters = { showFilters = true })
            }
        }
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)

        when {
            state.loading -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            state.rows.isEmpty() -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("Nothing matches these filters.", color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            else -> LazyColumn(
                state = listState,
                contentPadding = WindowInsets.navigationBars.asPaddingValues(),
                modifier = Modifier.fillMaxSize(),
            ) {
                state.rows.forEach { row ->
                    when (row) {
                        is ChecklistRow.Header -> stickyHeader(key = row.key, contentType = "header") {
                            SectionHeader(row, onClick = { vm.toggleSection(row.entry.id) })
                        }
                        is ChecklistRow.Task -> item(key = row.key, contentType = "task") {
                            TaskRow(
                                row,
                                onToggle = { vm.setDone(row.entry, !row.done) },
                                onInfo = { infoEntryId = row.entry.id },
                            )
                        }
                    }
                }
            }
        }
    }

    infoEntryId?.let { id ->
        vm.entry(id)?.let { entry ->
            EntryInfoSheet(
                app = app,
                gameId = gameId,
                entry = entry,
                done = entry.id in state.completed,
                onToggleDone = { vm.setDone(entry, it) },
                onDismiss = { infoEntryId = null },
            )
        }
    }

    if (showFilters) {
        FilterSheet(
            state = state,
            onStatus = vm::setStatus,
            onCategory = vm::setCategory,
            onDismiss = { showFilters = false },
        )
    }

    if (showTips) {
        AlertDialog(
            onDismissRequest = { showTips = false },
            confirmButton = { TextButton(onClick = { showTips = false }) { Text("Close") } },
            title = { Text("Guide tips") },
            text = {
                LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    state.tips.forEach { tip -> item { Text("•  $tip", style = MaterialTheme.typography.bodyMedium) } }
                }
            },
        )
    }

    if (confirmReset) {
        val sheet = state.sheets.getOrNull(state.selectedSheet)
        AlertDialog(
            onDismissRequest = { confirmReset = false },
            title = { Text("Reset progress?") },
            text = { Text("This unchecks all ${sheet?.done ?: 0} completed steps in ${sheet?.title}.") },
            confirmButton = {
                TextButton(onClick = { confirmReset = false; vm.resetSheet() }) {
                    Text("Reset", color = MaterialTheme.colorScheme.error)
                }
            },
            dismissButton = { TextButton(onClick = { confirmReset = false }) { Text("Cancel") } },
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SheetTabs(state: ChecklistUiState, onSelect: (Int) -> Unit) {
    PrimaryTabRow(
        selectedTabIndex = state.selectedSheet,
        containerColor = MaterialTheme.colorScheme.background,
    ) {
        state.sheets.forEachIndexed { i, sheet ->
            Tab(
                selected = i == state.selectedSheet,
                onClick = { onSelect(i) },
                selectedContentColor = MaterialTheme.colorScheme.primary,
                unselectedContentColor = MaterialTheme.colorScheme.onSurfaceVariant,
                text = {
                    Text(
                        sheet.title,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        fontWeight = if (i == state.selectedSheet) FontWeight.SemiBold else FontWeight.Normal,
                    )
                },
            )
        }
    }
}

@Composable
private fun ProgressSummary(state: ChecklistUiState) {
    val sheet = state.sheets.getOrNull(state.selectedSheet) ?: return
    val fraction by animateFloatAsState(if (sheet.total == 0) 0f else sheet.done.toFloat() / sheet.total, label = "progress")
    Column(Modifier.padding(horizontal = 16.dp, vertical = 12.dp)) {
        Row(verticalAlignment = Alignment.Bottom) {
            Text(
                percent(sheet.done, sheet.total),
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.primary,
            )
            Spacer(Modifier.width(8.dp))
            Text(
                "${sheet.done} of ${sheet.total} steps",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(bottom = 3.dp),
            )
        }
        Spacer(Modifier.height(8.dp))
        LinearProgressIndicator(
            progress = { fraction },
            modifier = Modifier.fillMaxWidth(),
            trackColor = MaterialTheme.colorScheme.surfaceVariant,
            drawStopIndicator = {},
        )
    }
}

@Composable
private fun SearchRow(state: ChecklistUiState, onQuery: (String) -> Unit, onOpenFilters: () -> Unit) {
    val activeFilters = (if (state.status != StatusFilter.All) 1 else 0) + (if (state.category != null) 1 else 0)
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier.fillMaxWidth().padding(start = 16.dp, end = 8.dp, bottom = 12.dp),
    ) {
        OutlinedTextField(
            value = state.query,
            onValueChange = onQuery,
            placeholder = { Text("Search items, places, notes") },
            leadingIcon = { Icon(Icons.Filled.Search, contentDescription = null) },
            trailingIcon = {
                if (state.query.isNotEmpty()) {
                    IconButton(onClick = { onQuery("") }) { Icon(Icons.Filled.Clear, contentDescription = "Clear search") }
                }
            },
            singleLine = true,
            shape = RoundedCornerShape(12.dp),
            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
            colors = OutlinedTextFieldDefaults.colors(
                unfocusedBorderColor = MaterialTheme.colorScheme.outline,
                unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                focusedContainerColor = MaterialTheme.colorScheme.surface,
            ),
            modifier = Modifier.weight(1f),
        )
        IconButton(onClick = onOpenFilters, modifier = Modifier.padding(start = 4.dp)) {
            BadgedBox(badge = { if (activeFilters > 0) Badge { Text("$activeFilters") } }) {
                Icon(
                    Icons.Filled.FilterList,
                    contentDescription = "Filters",
                    tint = if (activeFilters > 0) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun SectionHeader(row: ChecklistRow.Header, onClick: () -> Unit) {
    val rotation by animateFloatAsState(if (row.collapsed) -90f else 0f, label = "chevron")
    val complete = row.total > 0 && row.done == row.total
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surfaceVariant)
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 10.dp),
    ) {
        Icon(
            Icons.Filled.KeyboardArrowDown,
            contentDescription = if (row.collapsed) "Expand" else "Collapse",
            tint = MaterialTheme.colorScheme.primary,
            modifier = Modifier.rotate(rotation),
        )
        Spacer(Modifier.width(8.dp))
        Text(
            row.entry.item,
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.primary,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier.weight(1f),
        )
        Text(
            "${row.done}/${row.total}",
            style = MaterialTheme.typography.labelMedium,
            color = if (complete) MaterialTheme.colorScheme.tertiary else MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun TaskRow(row: ChecklistRow.Task, onToggle: () -> Unit, onInfo: () -> Unit) {
    val e = row.entry
    val dim = if (row.done) 0.5f else 1f
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onInfo)
            .padding(start = 4.dp, end = 4.dp, top = 2.dp, bottom = 2.dp),
    ) {
        Checkbox(
            checked = row.done,
            onCheckedChange = { onToggle() },
            colors = CheckboxDefaults.colors(
                checkedColor = MaterialTheme.colorScheme.primary,
                checkmarkColor = MaterialTheme.colorScheme.onPrimary,
            ),
        )
        Column(Modifier.weight(1f).padding(vertical = 8.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    "${e.step}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = dim),
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    e.item,
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = dim),
                    textDecoration = if (row.done) TextDecoration.LineThrough else null,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.weight(1f, fill = false),
                )
                if (e.ng) {
                    Spacer(Modifier.width(6.dp))
                    NgBadge()
                }
            }
            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(top = 2.dp)) {
                Text(
                    e.category,
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.secondary.copy(alpha = dim),
                )
                if (e.location.isNotEmpty()) {
                    Spacer(Modifier.width(8.dp))
                    Icon(
                        Icons.Outlined.Place,
                        contentDescription = null,
                        modifier = Modifier.size(12.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = dim),
                    )
                    Spacer(Modifier.width(2.dp))
                    Text(
                        e.location,
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = dim),
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
            }
        }
        IconButton(onClick = onInfo) {
            Icon(Icons.Outlined.Info, contentDescription = "Notes and map", tint = MaterialTheme.colorScheme.primary.copy(alpha = 0.85f))
        }
    }
}

@Composable
fun NgBadge() {
    Text(
        "NG+",
        style = MaterialTheme.typography.labelSmall,
        color = Ember,
        fontWeight = FontWeight.Bold,
        modifier = Modifier
            .background(Ember.copy(alpha = 0.15f), RoundedCornerShape(4.dp))
            .padding(horizontal = 5.dp, vertical = 1.dp),
    )
}
