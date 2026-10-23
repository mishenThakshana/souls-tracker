package com.soulstracker.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringSetPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.progressDataStore by preferencesDataStore(name = "progress")

/** Completed entry ids, stored per game. */
class ProgressStore(private val context: Context) {

    private fun key(gameId: String) = stringSetPreferencesKey("done_$gameId")

    fun completed(gameId: String): Flow<Set<String>> =
        context.progressDataStore.data.map { it[key(gameId)] ?: emptySet() }

    suspend fun setDone(gameId: String, entryId: String, done: Boolean) {
        context.progressDataStore.edit { prefs ->
            val current = prefs[key(gameId)] ?: emptySet()
            prefs[key(gameId)] = if (done) current + entryId else current - entryId
        }
    }

    suspend fun reset(gameId: String, entryIds: Set<String>) {
        context.progressDataStore.edit { prefs ->
            prefs[key(gameId)] = (prefs[key(gameId)] ?: emptySet()) - entryIds
        }
    }
}
