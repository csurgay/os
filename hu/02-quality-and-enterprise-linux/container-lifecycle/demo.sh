#!/bin/bash
# demo.sh - image vs container vs volume, foreground processes, commit vs build.
# Run with Docker; with Podman, replace "docker" by "podman" (same options).
D=${D:-docker}
run() { echo "\$ $*"; "$@" 2>&1; }

case "$1" in
writable)
  run $D run --name c1 course/app:1.0 tool write notes.txt "written in container c1"
  run $D run --rm course/app:1.0 tool cat notes.txt
  run $D diff c1
  ;;
volume)
  run $D volume create appdata
  run $D run --rm -v appdata:/data course/app:1.0 tool write notes.txt "kept in the volume"
  run $D run --rm -v appdata:/data course/app:1.0 tool cat notes.txt
  ;;
foreground)
  run $D run -d --name fg course/app:1.0
  run $D run -d --name bg course/app:1.0 tool serve --daemon
  sleep 2
  run $D ps -a --filter name=fg --filter name=bg --format 'table {{.Names}}\t{{.Command}}\t{{.Status}}'
  run $D logs bg
  ;;
commit)
  run $D run --user 0 --name edit course/app:1.0 tool write /etc/app.conf "colour=blue"
  run $D commit edit course/app:1.1-manual
  run $D history course/app:1.1-manual
  run $D image inspect -f 'Cmd={{.Config.Cmd}} User={{.Config.User}}' course/app:1.0 course/app:1.1-manual
  ;;
tags)
  run $D tag course/app:1.0 registry.example.com/course/app:1.0
  run $D tag course/app:1.0 course/app
  run $D image ls --format 'table {{.Repository}}\t{{.Tag}}\t{{.ID}}' --filter reference='*/app' --filter reference='*/*/app'
  ;;
clean)
  $D rm -f c1 fg bg edit >/dev/null 2>&1
  $D volume rm appdata >/dev/null 2>&1
  $D rmi course/app:1.1-manual registry.example.com/course/app:1.0 course/app:latest >/dev/null 2>&1
  true
  ;;
esac
