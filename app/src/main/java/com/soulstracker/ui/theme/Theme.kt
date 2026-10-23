package com.soulstracker.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

val Gold = Color(0xFFD4B26A)
val GoldDim = Color(0xFF8C7B5A)
val Ink = Color(0xFF12100D)
val Ash = Color(0xFF1C1915)
val AshRaised = Color(0xFF26221C)
val Parchment = Color(0xFFE9E1CF)
val Faded = Color(0xFFA79E8B)
val Ember = Color(0xFFE0533D)
val Grace = Color(0xFF8FBF7F)

private val Colors = darkColorScheme(
    primary = Gold,
    onPrimary = Ink,
    primaryContainer = Color(0xFF3A3122),
    onPrimaryContainer = Gold,
    secondary = GoldDim,
    onSecondary = Ink,
    secondaryContainer = AshRaised,
    onSecondaryContainer = Parchment,
    tertiary = Grace,
    background = Ink,
    onBackground = Parchment,
    surface = Ash,
    onSurface = Parchment,
    surfaceVariant = AshRaised,
    onSurfaceVariant = Faded,
    surfaceContainer = Ash,
    surfaceContainerHigh = AshRaised,
    surfaceContainerLow = Ash,
    outline = Color(0xFF4A4233),
    outlineVariant = Color(0xFF332D24),
    error = Ember,
)

private val Serif = FontFamily.Serif

private val AppTypography = Typography().run {
    copy(
        headlineMedium = headlineMedium.copy(fontFamily = Serif, fontWeight = FontWeight.SemiBold),
        headlineSmall = headlineSmall.copy(fontFamily = Serif, fontWeight = FontWeight.SemiBold),
        titleLarge = titleLarge.copy(fontFamily = Serif, fontWeight = FontWeight.SemiBold),
        titleMedium = TextStyle(fontFamily = Serif, fontWeight = FontWeight.SemiBold, fontSize = 17.sp, lineHeight = 22.sp),
    )
}

@Composable
fun SoulsTrackerTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = Colors, typography = AppTypography, content = content)
}
