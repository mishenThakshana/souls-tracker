package com.soulstracker.data

import kotlinx.serialization.Serializable

@Serializable
data class Checklist(
    val game: String,
    val title: String,
    val tips: List<String> = emptyList(),
    val sheets: List<Sheet>,
)

/** One tab of a game's checklist, e.g. the base game or a DLC. */
@Serializable
data class Sheet(
    val id: String,
    val title: String,
    val entries: List<Entry>,
)

@Serializable
data class Entry(
    val id: String,
    val step: Int = 0,
    val item: String,
    val category: String = "",
    val location: String = "",
    val notes: String = "",
    /** Rows the guide uses as area headers; shown as section titles rather than tasks. */
    val section: Boolean = false,
    /** Guide marks this step as needing a later playthrough for all dialogue and items. */
    val ng: Boolean = false,
    /** Map layer the pin is on (M00 overworld, M01 underground, M10 Land of Shadow); null when there is no spot. */
    val map: String? = null,
    /** Pin position in full-resolution (10496 px) map pixels. */
    val x: Int = 0,
    val y: Int = 0,
    /** True when the red dot is the datamined position; false when it marks the stated area. */
    val precise: Boolean = false,
)

data class Game(
    val id: String,
    val title: String,
    val subtitle: String,
)

object GameCatalog {
    val games = listOf(
        Game(id = "eldenring", title = "Elden Ring", subtitle = "Base game · Shadow of the Erdtree"),
    )

    fun find(id: String): Game = games.first { it.id == id }
}
