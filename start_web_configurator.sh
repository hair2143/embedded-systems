#!/usr/bin/env bash
echo "Starting Pico MacroPad Web Configurator on http://localhost:8000..."
python3 -m http.server 8000 -d web-configurator
