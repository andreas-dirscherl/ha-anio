# Anio Smartwatch Integration für Home Assistant

Eine HACS-kompatible Custom Integration zur Einbindung der **Anio 6** (und kompatibler Anio Kinder-Smartwatches) in Home Assistant.

## Features

- 📍 **Device Tracker (`device_tracker`)**: Präzises GPS/LBS-Tracking der Uhr auf der HA-Karte.
- 🔋 **Akkustand Sensor (`sensor`)**: Prozentualer Ladestand & Ladezustand (`binary_sensor`).
- 📶 **Empfangsstärke Sensor (`sensor`)**: GSM-Signalstärke in dBm.
- 🌐 **Online Status (`binary_sensor`)**: Zeigt an, ob die Uhr aktuell mit der Anio Cloud verbunden ist.
- 🏫 **Schulmodus Switch (`switch`)**: Ruhemodus / Schulmodus direkt aus HA aktivieren oder deaktivieren.
- 🔔 **Uhr suchen Button (`button`)**: Triggert den Suchton der Uhr, um sie schnell wiederzufinden.
- ⚡ **Remote Power-Off Button (`button`)**: Uhr aus der Ferne ausschalten.
- 🔐 **Bequeme Einrichtung**: Vollständiger UI Config Flow mit E-Mail und Passwort im HA-Frontend.

## Installation via HACS

1. Öffne **HACS** in Home Assistant.
2. Klicke oben rechts auf die drei Punkte **⋮** -> **Benutzerdefinierte Repositories**.
3. Füge die Repository-URL hinzu:
   `https://github.com/andreas-dirscherl/ha-anio`
   Kategorie: **Integration**
4. Klicke auf **Hinzufügen**, wähle **Anio Smartwatch** aus und klicke auf **Herunterladen**.
5. Starte Home Assistant neu.

## Konfiguration

1. Gehe in Home Assistant zu **Einstellungen** -> **Geräte & Dienste** -> **Integration hinzufügen**.
2. Suche nach **Anio Smartwatch**.
3. Gib deine Anio Cloud E-Mail-Adresse und dein Passwort ein.
4. Fertig! Die Uhr(en) werden automatisch als Geräte mit allen Entitäten angelegt.

## Lizenz

MIT License
