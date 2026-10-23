package com.soulstracker.ui.checklist

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.outlined.Place
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import com.soulstracker.SoulsTrackerApp
import com.soulstracker.data.Entry
import com.soulstracker.data.MapCropRenderer
import com.soulstracker.ui.theme.Ember

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EntryInfoSheet(
    app: SoulsTrackerApp,
    gameId: String,
    entry: Entry,
    done: Boolean,
    onToggleDone: (Boolean) -> Unit,
    onDismiss: () -> Unit,
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        modifier = Modifier.statusBarsPadding(),
        sheetState = sheetState,
        containerColor = MaterialTheme.colorScheme.surface,
    ) {
        Column(
            Modifier
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
                .navigationBarsPadding()
                .padding(bottom = 16.dp),
        ) {
            Text(
                "Step ${entry.step}",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(entry.item, style = MaterialTheme.typography.headlineSmall, color = MaterialTheme.colorScheme.primary)
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (entry.category.isNotEmpty()) InfoChip(entry.category)
                if (entry.location.isNotEmpty()) InfoChip(entry.location, place = true)
            }
            if (entry.ng) {
                Spacer(Modifier.height(10.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    NgBadge()
                    Spacer(Modifier.width(8.dp))
                    Text(
                        "Repeat on a later playthrough to get all dialogue and items.",
                        style = MaterialTheme.typography.bodySmall,
                        color = Ember,
                    )
                }
            }

            Spacer(Modifier.height(18.dp))
            Text("Notes", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(4.dp))
            Text(
                entry.notes.ifEmpty { "No notes for this step." },
                style = MaterialTheme.typography.bodyLarge,
                color = if (entry.notes.isEmpty()) MaterialTheme.colorScheme.onSurfaceVariant else MaterialTheme.colorScheme.onSurface,
            )

            if (entry.map != null) {
                Spacer(Modifier.height(18.dp))
                Text("Location", style = MaterialTheme.typography.titleMedium)
                Spacer(Modifier.height(8.dp))
                MapCrop(app, gameId, entry)
                Spacer(Modifier.height(6.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        Modifier
                            .size(8.dp)
                            .clip(CircleShape)
                            .background(Ember),
                    )
                    Spacer(Modifier.width(6.dp))
                    Text(
                        if (entry.precise) "Red dot marks the exact spot." else "Red ring marks the general area (${entry.location}).",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                Text(
                    "Pinch to zoom · double-tap to reset",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                )
            } else {
                Spacer(Modifier.height(18.dp))
                Text("Location", style = MaterialTheme.typography.titleMedium)
                Spacer(Modifier.height(4.dp))
                Text(
                    "This step isn't tied to one spot on the map.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            Spacer(Modifier.height(20.dp))
            if (done) {
                OutlinedButton(onClick = { onToggleDone(false) }, modifier = Modifier.fillMaxWidth()) {
                    Text("Mark as not done")
                }
            } else {
                Button(
                    onClick = { onToggleDone(true); onDismiss() },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                ) {
                    Icon(Icons.Filled.Check, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Mark as done")
                }
            }
        }
    }
}

@Composable
private fun InfoChip(text: String, place: Boolean = false) {
    AssistChip(
        onClick = {},
        label = { Text(text) },
        leadingIcon = if (place) {
            { Icon(Icons.Outlined.Place, contentDescription = null, modifier = Modifier.size(16.dp)) }
        } else null,
        colors = AssistChipDefaults.assistChipColors(
            labelColor = MaterialTheme.colorScheme.onSurface,
            leadingIconContentColor = MaterialTheme.colorScheme.primary,
        ),
    )
}

@Composable
private fun MapCrop(app: SoulsTrackerApp, gameId: String, entry: Entry) {
    val bitmap by produceState<ImageBitmap?>(null, entry.id) { value = app.repository.loadMap(gameId, entry) }
    var scale by remember(entry.id) { mutableFloatStateOf(1f) }
    var offset by remember(entry.id) { mutableStateOf(Offset.Zero) }

    Box(
        contentAlignment = Alignment.Center,
        modifier = Modifier
            .fillMaxWidth()
            .aspectRatio(MapCropRenderer.WIDTH.toFloat() / MapCropRenderer.HEIGHT)
            .clip(RoundedCornerShape(12.dp))
            .background(MaterialTheme.colorScheme.background)
            .pointerInput(entry.id) {
                detectTransformGestures { _, pan, zoom, _ ->
                    scale = (scale * zoom).coerceIn(1f, 4f)
                    val maxX = size.width * (scale - 1) / 2
                    val maxY = size.height * (scale - 1) / 2
                    offset = Offset(
                        (offset.x + pan.x).coerceIn(-maxX, maxX),
                        (offset.y + pan.y).coerceIn(-maxY, maxY),
                    )
                }
            }
            .pointerInput(entry.id) {
                detectTapGestures(onDoubleTap = { scale = 1f; offset = Offset.Zero })
            },
    ) {
        val bmp = bitmap
        if (bmp == null) {
            CircularProgressIndicator(Modifier.size(28.dp))
        } else {
            Image(
                bitmap = bmp,
                contentDescription = "Map location",
                contentScale = ContentScale.Crop,
                modifier = Modifier
                    .fillMaxWidth()
                    .graphicsLayer {
                        scaleX = scale
                        scaleY = scale
                        translationX = offset.x
                        translationY = offset.y
                    },
            )
        }
    }
}
