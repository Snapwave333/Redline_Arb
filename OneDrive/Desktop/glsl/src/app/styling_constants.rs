/// Centralized styling constants and helpers for HUD rendering
pub struct StylingConstants;

impl StylingConstants {
    // Neon color palette
    pub const NEON_PINK: (u8, u8, u8) = (255, 0, 180); // Vibrant Neon Pink/Purple
    pub const ELECTRIC_BLUE: (u8, u8, u8) = (0, 180, 255);
    pub const BRIGHT_ORANGE: (u8, u8, u8) = (255, 140, 0);
    pub const ALERT_RED: (u8, u8, u8) = (255, 0, 0);
    pub const LIME_GREEN: (u8, u8, u8) = (0, 235, 100);
    pub const WHITE: (u8, u8, u8) = (250, 250, 250);
    pub const NEAR_BLACK: (u8, u8, u8) = (10, 10, 10);

    // Block/separator styling
    pub const FULL_BLOCK: char = '█';
    pub const PIPE_SEP: &'static str = "|";

    // ANSI helpers
    pub fn fg(rgb: (u8, u8, u8)) -> String {
        format!("\x1b[38;2;{};{};{}m", rgb.0, rgb.1, rgb.2)
    }
    pub fn bg(rgb: (u8, u8, u8)) -> String {
        format!("\x1b[48;2;{};{};{}m", rgb.0, rgb.1, rgb.2)
    }
    pub fn reset() -> &'static str {
        "\x1b[0m"
    }
}