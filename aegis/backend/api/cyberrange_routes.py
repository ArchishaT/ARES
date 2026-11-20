"""
REST API routes for the abstracted cyber range (red team / blue team).
Mounted at /api/cyberrange. Includes a minimal notetaker endpoint so
session notes can be saved server-side as well as in browser storage.
"""
from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from cyberrange.models import BlueTeamRunRequest, BlueTeamResult, RedTeamRunRequest, RedTeamResult
from cyberrange.simulator import run_blue_team, run_red_team

router = APIRouter()


class NoteIn(BaseModel):
    title: str
    body: str


class Note(NoteIn):
    id: int
    created_at: str


_notes: List[Note] = []
_next_id = 1


@router.post("/cyberrange/red-team/run", response_model=RedTeamResult)
def red_team_run(req: RedTeamRunRequest) -> RedTeamResult:
    return run_red_team(req.system, req.techniques, req.seed)


@router.post("/cyberrange/blue-team/run", response_model=BlueTeamResult)
def blue_team_run(req: BlueTeamRunRequest) -> BlueTeamResult:
    return run_blue_team(req.vulnerability, req.system, req.duration_ticks, req.seed)


@router.get("/cyberrange/techniques")
def list_techniques() -> dict:
    return {
        "techniques": [
            {"id": "port_scan", "label": "Port Scan", "description": "Enumerate reachable services on the target."},
            {"id": "brute_force_login", "label": "Brute-Force Login", "description": "Guess credentials against an exposed login."},
            {"id": "phishing_foothold", "label": "Phishing Foothold", "description": "Social-engineer an initial foothold."},
            {"id": "privilege_escalation", "label": "Privilege Escalation", "description": "Escalate from a foothold to elevated privileges."},
            {"id": "lateral_movement", "label": "Lateral Movement", "description": "Move from the compromised host to others on the network."},
            {"id": "data_exfiltration", "label": "Data Exfiltration", "description": "Extract data from the compromised system."},
        ]
    }


@router.get("/cyberrange/vulnerabilities")
def list_vulnerabilities() -> dict:
    return {
        "vulnerabilities": [
            {"id": "trojan", "label": "Trojan", "description": "Disguised malicious process triggered early, detected mainly by monitoring."},
            {"id": "backdoor", "label": "Backdoor", "description": "Hidden persistent access point, slow-burn, best countered by strong authentication."},
            {"id": "time_bomb", "label": "Time Bomb", "description": "Dormant payload that triggers on a schedule and degrades quickly once active."},
            {"id": "worm", "label": "Worm", "description": "Self-propagating threat, contained primarily by network segmentation."},
            {"id": "rootkit", "label": "Rootkit", "description": "Deeply hidden, slow to detect; needs patching and least-privilege to root out."},
        ]
    }


# -- notetaker -----------------------------------------------------------
@router.get("/notes", response_model=List[Note])
def list_notes() -> List[Note]:
    return _notes


@router.post("/notes", response_model=Note)
def create_note(note: NoteIn) -> Note:
    global _next_id
    rec = Note(id=_next_id, created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), **note.model_dump())
    _notes.append(rec)
    _next_id += 1
    return rec


@router.delete("/notes/{note_id}")
def delete_note(note_id: int) -> dict:
    global _notes
    _notes = [n for n in _notes if n.id != note_id]
    return {"ok": True}
