package com.soulstracker.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.LruCache
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json

/** Reads checklists and map tiles bundled in assets/<gameId>/. */
class ChecklistRepository(private val context: Context) {
    private val json = Json { ignoreUnknownKeys = true }
    private val cache = mutableMapOf<String, Checklist>()
    private val mutex = Mutex()

    suspend fun load(gameId: String): Checklist = mutex.withLock {
        cache.getOrPut(gameId) {
            withContext(Dispatchers.IO) {
                context.assets.open("$gameId/checklist.json").bufferedReader().use {
                    json.decodeFromString<Checklist>(it.readText())
                }
            }
        }
    }

    // Decoded 256 px tiles; a crop touches at most 9, and nearby steps share tiles.
    private val tiles = object : LruCache<String, Bitmap>(32) {}

    suspend fun loadMap(gameId: String, entry: Entry): ImageBitmap? = withContext(Dispatchers.IO) {
        MapCropRenderer.render(entry) { map, tx, ty -> tile(gameId, map, tx, ty) }?.asImageBitmap()
    }

    private fun tile(gameId: String, map: String, tx: Int, ty: Int): Bitmap? {
        val key = "$gameId/tiles/$map/${ty}_$tx.webp"
        tiles.get(key)?.let { return it }
        // Ocean tiles are not bundled; the renderer leaves those as background.
        val bitmap = runCatching { context.assets.open(key).use { BitmapFactory.decodeStream(it) } }.getOrNull()
        return bitmap?.also { tiles.put(key, it) }
    }
}
