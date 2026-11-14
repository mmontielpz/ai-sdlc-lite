#!/bin/sh
# PLACEHOLDER for a project-owned runner wrapper. AI-SDLC Lite never executes it (the file is not executable).
# A real project supplies its own wrapper, which must refuse the primary checkout, use a private HOME/XDG profile so
# user:// cannot reach real saves, and pass the project's own safety flags. This stub does nothing.
echo "placeholder runner: replace with the project's own approved wrapper" >&2
exit 64
