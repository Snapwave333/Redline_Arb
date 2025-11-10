use super::DebugLog;
use anyhow::Result;
use chroma::ascii::{AsciiConverter, AsciiPalette};
use chroma::params::{PaletteType, ShaderParams};
use crossterm::event::{self, Event, KeyCode, KeyEvent, KeyEventKind};
use crossterm::{cursor, execute, style, terminal};
use std::io::{stdout, Write};
use std::time::Duration;

/// Handle keyboard input events
pub fn handle_input(
  params: &mut ShaderParams,
  converter: &mut AsciiConverter,
  running: &mut bool,
  debug_log: &mut DebugLog,
  exit_confirmation: bool,
  show_status_bar: &mut bool,
) -> Result<()> {
  if !event::poll(Duration::from_millis(0))? {
    return Ok(());
  }

  if let Event::Key(KeyEvent {
    code,
    kind: KeyEventKind::Press,
    ..
  }) = event::read()?
  {
    handle_key_press(code, params, converter, running, debug_log, exit_confirmation, show_status_bar)?;
  }

  Ok(())
}

/// Handle individual key press events
fn handle_key_press(
  code: KeyCode,
  params: &mut ShaderParams,
  converter: &mut AsciiConverter,
  running: &mut bool,
  debug_log: &mut DebugLog,
  exit_confirmation: bool,
  show_status_bar: &mut bool,
) -> Result<()> {
  match code {
    // Quit
    KeyCode::Char('q') | KeyCode::Char('Q') | KeyCode::Esc => {
      if exit_confirmation {
        if confirm_exit()? {
          *running = false;
        }
      } else {
        *running = false;
      }
    }

    // Toggle futuristic status bar visibility
    KeyCode::Char('h') | KeyCode::Char('H') => {
      *show_status_bar = !*show_status_bar;
      writeln!(
        debug_log,
        "UI: Futuristic status bar {}",
        if *show_status_bar { "shown" } else { "hidden" }
      )?;
    }

    // Parameter adjustments (disabled when audio mode is active)
    KeyCode::Up => {
      if !params.audio_enabled {
        params.frequency += 0.1;
      }
    }
    KeyCode::Down => {
      if !params.audio_enabled {
        params.frequency = (params.frequency - 0.1).max(0.1);
      }
    }
    KeyCode::Right => {
      if !params.audio_enabled {
        params.speed += 0.1;
      }
    }
    KeyCode::Left => {
      if !params.audio_enabled {
        params.speed = (params.speed - 0.1).max(0.1);
      }
    }
    KeyCode::Char('+') | KeyCode::Char('=') => {
      if !params.audio_enabled {
        params.amplitude += 0.1;
      }
    }
    KeyCode::Char('-') | KeyCode::Char('_') => {
      if !params.audio_enabled {
        params.amplitude = (params.amplitude - 0.1).max(0.1);
      }
    }
    KeyCode::Char('[') => params.scale = (params.scale - 0.1).max(0.1),
    KeyCode::Char(']') => params.scale += 0.1,

    // Pattern selection
    KeyCode::Char('t') | KeyCode::Char('T') => {
      params.pattern_type = params.pattern_type.next();
    }

    // Color mode selection
    KeyCode::Char('c') | KeyCode::Char('C') => {
      params.color_mode = params.color_mode.next();
    }

    // Palette type selection
    KeyCode::Char('p') | KeyCode::Char('P') => {
      params.palette = params.palette.next();
      let new_palette = palette_from_type(params.palette);
      converter.set_palette(new_palette);
    }

    // Randomization
    KeyCode::Char('r') | KeyCode::Char('R') => {
      params.randomize();

      let new_palette = palette_from_type(params.palette);

      converter.set_palette(new_palette);
    }

    // Trigger a manual beat (start beat effects)
    KeyCode::Char('b') | KeyCode::Char('B') => {
      params.beat_distortion_time = params.time; // start beat window
      // Keep existing strengths but ensure zoom has a minimum
      params.beat_zoom_strength = params.beat_zoom_strength.max(0.4);

      writeln!(
        debug_log,
        "BEAT: Triggered (time {:.2}, zoom_strength {:.2})",
        params.beat_distortion_time,
        params.beat_zoom_strength
      )?;
    }

    // Cycle through effects
    KeyCode::Char('n') | KeyCode::Char('N') => {
      let mut next = (params.effect_type + 1) % 7;

      if next == 0 || next == 1 {
        next = 2;
      }

      params.effect_type = next;
      params.effect_time = params.time;

      writeln!(
        debug_log,
        "EFFECT: Switched to effect type {}",
        params.effect_type
      )?;
    }

    // Audio toggle
    KeyCode::Char('a') | KeyCode::Char('A') => {
      #[cfg(feature = "audio")]
      {
        params.audio_enabled = !params.audio_enabled;

        writeln!(
          debug_log,
          "AUDIO: Audio reactivity {}",
          if params.audio_enabled {
            "enabled"
          } else {
            "disabled"
          }
        )?;
      }
    }

    // Save configuration
    KeyCode::Char('s') | KeyCode::Char('S') => match params.save_to_file() {
      Ok(filename) => {
        writeln!(debug_log, "CONFIG: Saved configuration to {}", filename)?;
      }
      Err(error) => {
        writeln!(debug_log, "CONFIG: Failed to save configuration: {}", error)?;
      }
    },

    _ => {}
  }

  Ok(())
}

/// Convert palette type to ASCII palette
fn palette_from_type(palette_type: PaletteType) -> AsciiPalette {
  match palette_type {
    PaletteType::Standard => AsciiPalette::standard(),
    PaletteType::Blocks => AsciiPalette::blocks(),
    PaletteType::Circles => AsciiPalette::circles(),
    PaletteType::Smooth => AsciiPalette::smooth(),
    PaletteType::Braille => AsciiPalette::braille(),
    PaletteType::Geometric => AsciiPalette::geometric(),
    PaletteType::Mixed => AsciiPalette::mixed(),
    PaletteType::Dots => AsciiPalette::dots(),
    PaletteType::Shades => AsciiPalette::shades(),
    PaletteType::Lines => AsciiPalette::lines(),
    PaletteType::Triangles => AsciiPalette::triangles(),
    PaletteType::Arrows => AsciiPalette::arrows(),
    PaletteType::Powerline => AsciiPalette::powerline(),
    PaletteType::BoxDraw => AsciiPalette::boxdraw(),
    PaletteType::Extended => AsciiPalette::extended(),
    PaletteType::Simple => AsciiPalette::simple(),
  }
}

/// Confirm exit with user
fn confirm_exit() -> Result<bool> {
  let (width, height) = terminal::size()?;
  let message = "Really quit? (Y/N)";
  let x = (width.saturating_sub(message.len() as u16)) / 2;
  let y = height / 2;

  // Save cursor position
  execute!(stdout(), cursor::SavePosition)?;
  
  // Move to center and show message
  execute!(
    stdout(),
    cursor::MoveTo(x, y),
    style::SetForegroundColor(style::Color::Yellow),
    style::Print(message),
    cursor::RestorePosition
  )?;

  // Wait for Y/N input
  loop {
    if event::poll(Duration::from_millis(100))? {
      if let Event::Key(KeyEvent {
        code,
        kind: KeyEventKind::Press,
        ..
      }) = event::read()?
      {
        match code {
          KeyCode::Char('y') | KeyCode::Char('Y') => {
            // Clear the message
            execute!(
              stdout(),
              cursor::MoveTo(x, y),
              style::Print(" ".repeat(message.len())),
              cursor::RestorePosition
            )?;
            return Ok(true);
          }
          KeyCode::Char('n') | KeyCode::Char('N') | KeyCode::Esc => {
            // Clear the message
            execute!(
              stdout(),
              cursor::MoveTo(x, y),
              style::Print(" ".repeat(message.len())),
              cursor::RestorePosition
            )?;
            return Ok(false);
          }
          _ => {} // Ignore other keys
        }
      }
    }
  }
}
