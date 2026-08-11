# Handoff: PRD härten vor Loki-Mode

**Wo ausführen:** lokal, in einer Umgebung mit installiertem `codex`.
**Warum lokal:** `/autoplan` fährt pro Review-Phase zwei unabhängige Reviewer (Claude-Subagent + Codex). Ohne Codex läuft nur einer — der adversariale Wert halbiert sich.

**Setup:**
```bash
git clone <repo> && cd move-on
git checkout claude/prd-check-pidhpa
which codex   # muss einen Pfad ausgeben
```

Dann den Block unten in Claude Code einfügen.

---

## Prompt zum Kopieren

```
Ziel: docs/PRD-v0.1.md so härten, dass ein Build-Agent es ohne Rückfragen
und ohne Raten umsetzen kann. Das PRD ist der einzige Input für den Build —
alles, was hier unklar ist, wird falsch gebaut.

Harte Randbedingung: Der v0.1-Scope ist FIX. Extract + Erase, sonst nichts.
Distill (v0.2) und Deploy (v1.0) bleiben ausgeschlossen. Skills, die Scope
öffnen wollen, dürfen den Wedge hinterfragen, aber nichts in v0.1
hineinverhandeln.

Ablauf, in dieser Reihenfolge:

1. /office-hours — Startup-Mode. Prüfe das Fundament: Wer ist verzweifelt
   genug, ein Extract+Erase-Tool ohne Distill zu benutzen? Das PRD ist beim
   "Was" sehr präzise und beim "Wer/Warum" stumm. Scope bleibt fix, nur der
   Wedge wird validiert. Das Design-Doc, das dieser Schritt speichert, wird
   von /autoplan in Step 2 automatisch eingelesen — deshalb zuerst.

2. /autoplan — auf docs/PRD-v0.1.md. Erwartete Scope-Detection:
   DX-Scope ja (CLI, flags, pip, package), UI-Scope nein (kein Design-Review).
   Läuft bis "## GSTACK REVIEW REPORT" in der Plan-Datei steht.

3. /cso — Threat Model auf die gehärtete Fassung. Schwerpunkt: das
   Privacy-Versprechen ist der Produktkern, aber FR-7 deckt nur ausgehende
   Sockets ab. Ungelöst: MOVEON.d/raw/ enthält den kompletten Chatverlauf im
   Klartext im Arbeitsverzeichnis. Nichts im PRD spricht über .gitignore,
   Warnung beim Anlegen, oder Dateirechte. Ein Nutzer, der sein Bundle
   versehentlich committet, ist ein Produkt-Totalschaden.

4. /learn — die getroffenen Entscheidungen als Learnings festschreiben.
   Die gstack-Preamble lädt sie in jeden späteren Skill-Run, damit erbt der
   Build-Agent sie automatisch. Das ist der Übergabekanal an Loki.

Vor Schritt 1: die drei Selbstwidersprüche unten direkt im PRD fixen.
Das sind keine Geschmacksfragen, die brauchen keinen Review.
```

---

## Blocker — vor dem Pipeline-Start fixen

Selbstwidersprüche im PRD. Nicht reviewbedürftig, nur zu entscheiden:

1. **"5 Befehle" sind 4.** Die Completion-Checklist verlangt `moveon --help` zeigt "die 5 Befehle extract, guide, erase, status" — das sind vier. `erase --all` ist ein Flag, kein Befehl. Zusätzlich verlangt dieselbe Zeile "und die Version", aber `--version` taucht in der CLI-Oberfläche nirgends auf. Eine Checkliste, die deterministisch prüfbar sein soll, darf so nicht dastehen.

2. **`messages.jsonl`-Schema ist mehrdeutig.** FR-1 sagt "eine JSONL-Zeile pro Nachricht", das Schema zeigt aber `{"messages": [...]}` — ein Array pro Zeile. Ein Element pro Array? Oder doch eine Konversation pro Zeile? Ohne Entscheidung rät der Build-Agent, und es fällt erst beim Mem0-Import auf.

3. **FR-6 widerspricht sich.** Manifest enthält "pro Quelle" einen Eintrag, soll aber gleichzeitig "die Historie beider Läufe" behalten. Beides zusammen braucht ein `runs[]`-Schema, das nicht spezifiziert ist.

## Weitere Lücken — kommen in den Reviews hoch

Hier gelistet, damit sie nicht durchrutschen:

4. **Grösstes Baurisiko: das Anthropic-Exportformat.** Das PRD gibt selbst zu, es nicht genau zu kennen. Fixtures sollen aus "öffentlich dokumentierten Formatbeschreibungen" synthetisiert werden — aber ob der Build-Agent dafür recherchieren darf, steht nirgends. Wenn nicht, entsteht ein Parser, der gegen ein erfundenes Format grün testet.

5. **Die Einreichungskanäle in FR-5 sind Faktenbehauptungen.** Ein Agent, der eine Datenschutz-Kontaktadresse halluziniert, produziert Löschanträge, die ins Leere gehen. Braucht eine Quelle-der-Wahrheit-Entscheidung, kein Modellwissen.

6. **`--out DIR` ist unterspezifiziert.** Elternverzeichnis von `MOVEON.d/` oder das Bundle-Verzeichnis selbst? Und `status` hat gar kein `--out` — liest also ausschliesslich `./MOVEON.d/`?

7. **FR-3 "registriert ist".** Entry-Points, Registry-Dict, Auto-Discovery? Unspezifiziert — und es ist der einzige Erweiterungspunkt des Produkts.

8. **Grosse Exports.** ChatGPT-`conversations.json` wird schnell dreistellig-MB. Streaming oder komplett in den RAM? Nicht spezifiziert.

## Gate — wann Loki starten darf

Alles davon muss gelten:

- [ ] `docs/PRD-v0.1.md` endet mit `## GSTACK REVIEW REPORT` (autoplan durchgelaufen, nicht abgebrochen)
- [ ] Punkte 1–8 oben aufgelöst — im PRD-Text, nicht im Sessionverlauf
- [ ] Jede FR hat mindestens ein Given/When/Then, das ohne Interpretation prüfbar ist
- [ ] Completion-Checklist ist zeilenweise maschinell verifizierbar (jede Zeile = ein Kommando mit Exit-Code)
- [ ] CSO-Findings eingearbeitet oder bewusst als Non-Goal notiert
- [ ] Entscheidungen liegen in `/learn`, nicht nur im Chat
