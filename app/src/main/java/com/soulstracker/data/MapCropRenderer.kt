package com.soulstracker.data

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RadialGradient
import android.graphics.Shader

/**
 * Cuts an entry's map crop out of the bundled zoom-5 tiles (half of the 10496 px master map)
 * and draws the red location marker. Sizes must match tools/pack_tiles.py.
 */
object MapCropRenderer {
    const val WIDTH = 576
    const val HEIGHT = 360
    private const val MAP_SIZE = 5248
    private const val TILE = 256
    private const val BACKGROUND = 0xFF0E0D0B.toInt()

    private val red = 0xFFE61414.toInt()
    private val white = 0xFFFFFFFF.toInt()

    fun render(entry: Entry, tile: (map: String, tx: Int, ty: Int) -> Bitmap?): Bitmap? {
        val map = entry.map ?: return null
        val cx = entry.x / 2f
        val cy = entry.y / 2f
        val x0 = (cx - WIDTH / 2f).toInt().coerceIn(0, MAP_SIZE - WIDTH)
        val y0 = (cy - HEIGHT / 2f).toInt().coerceIn(0, MAP_SIZE - HEIGHT)

        val out = Bitmap.createBitmap(WIDTH, HEIGHT, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(out)
        canvas.drawColor(BACKGROUND)
        for (ty in y0 / TILE..(y0 + HEIGHT) / TILE) {
            for (tx in x0 / TILE..(x0 + WIDTH) / TILE) {
                tile(map, tx, ty)?.let { canvas.drawBitmap(it, (tx * TILE - x0).toFloat(), (ty * TILE - y0).toFloat(), null) }
            }
        }
        drawMarker(canvas, cx - x0, cy - y0, entry.precise)
        return out
    }

    private fun drawMarker(canvas: Canvas, x: Float, y: Float, precise: Boolean) {
        val fill = Paint(Paint.ANTI_ALIAS_FLAG)
        val stroke = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.STROKE }
        if (precise) {
            fill.shader = RadialGradient(x, y, 24f, 0x99FF1E1E.toInt(), 0x00FF1E1E, Shader.TileMode.CLAMP)
            canvas.drawCircle(x, y, 24f, fill)
            fill.shader = null
            fill.color = red
            canvas.drawCircle(x, y, 8f, fill)
            stroke.color = white
            stroke.strokeWidth = 2f
            canvas.drawCircle(x, y, 8f, stroke)
        } else {
            val r = 46f
            fill.color = 0x3CFF1E1E
            canvas.drawCircle(x, y, r, fill)
            stroke.color = 0xFFEB1E1E.toInt()
            stroke.strokeWidth = 3f
            canvas.drawCircle(x, y, r, stroke)
            fill.color = red
            canvas.drawCircle(x, y, 5f, fill)
            stroke.color = white
            stroke.strokeWidth = 2f
            canvas.drawCircle(x, y, 5f, stroke)
        }
    }
}
