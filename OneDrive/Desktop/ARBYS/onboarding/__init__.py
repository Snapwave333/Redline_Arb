"""
Onboarding system for ARBYS application.

Provides first-run experience including splash screen, welcome dialog,
guided tutorial, and centralized tooltips.
"""

__version__ = "1.0.0"

from onboarding.first_run_manager import load_flags, save_flags
from onboarding.splash_screen import Splash
from onboarding.tooltips import TOOLTIPS, apply_tooltips
from onboarding.tutorial_overlay import OnboardingTour
from onboarding.welcome_dialog import WelcomeDialog
from onboarding.wiring_example import bootstrap_app

__all__ = [
    "load_flags",
    "save_flags",
    "Splash",
    "WelcomeDialog",
    "OnboardingTour",
    "TOOLTIPS",
    "apply_tooltips",
    "bootstrap_app",
]
