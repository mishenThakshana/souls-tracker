package com.soulstracker

import android.app.Application
import com.soulstracker.data.ChecklistRepository
import com.soulstracker.data.ProgressStore

class SoulsTrackerApp : Application() {
    val repository by lazy { ChecklistRepository(this) }
    val progress by lazy { ProgressStore(this) }
}
