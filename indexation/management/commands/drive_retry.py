"""Reessaie l'envoi Drive des videos gardees en local (dossier downloaded_videos).

Affiche le detail compte par compte (auth, quota, envoi) puis leve le blocage
si tout est parti. A lancer quand le site affiche « BLOQUE : Echec d'envoi
repete ... » ou apres une reautorisation des comptes Google.
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from indexation import drive


class Command(BaseCommand):
    help = "Renvoie sur Drive les videos locales en attente et debloque le pipeline."

    def handle(self, *args, **options):
        videos_dir = Path(getattr(settings, "VIDEOS_DIR"))
        pending = sorted(videos_dir.glob("video_*.mp4")) if videos_dir.exists() else []
        self.stdout.write(f"{len(pending)} video(s) en attente dans {videos_dir}")
        if not pending:
            self.stdout.write("Rien a envoyer.")

        sent, kept, problem = drive.flush_pending_videos(
            log=lambda m: self.stdout.write(m))

        state = drive.load_state()
        if kept == 0:
            state["blocked"] = False
            state["reason"] = ""
            drive.save_state(state)
            self.stdout.write(self.style.SUCCESS(
                f"OK : {sent} envoyee(s), 0 gardee. Blocage leve, vous pouvez relancer un JSON."))
        else:
            state["blocked"] = True
            state["reason"] = f"Dernier probleme : {problem}"
            drive.save_state(state)
            self.stdout.write(self.style.ERROR(
                f"{sent} envoyee(s), {kept} gardee(s) : {problem}"))
