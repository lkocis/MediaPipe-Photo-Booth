# Pokretanje Photo Booth-a u Dockeru

## Preduvjeti

- Docker Desktop instaliran
- Model fajlovi u root folderu: `face_landmarker.task`, `hand_landmarker.task`

---

## Linux

```bash
# Dozvoli Dockeru pristup ekranu
xhost +local:docker

# Izgradi i pokreni
docker build -t photo-booth .
docker compose up
```

---

## Windows

**Korak 1** — Instaliraj [VcXsrv](https://sourceforge.net/projects/vcxsrv/)

**Korak 2** — Pokreni XLaunch s ovim postavkama:

- Multiple windows
- Display number: `0`
- Označi Disable access control

**Korak 3** — Pokreni container:

```bash
docker build -t photo-booth .
docker compose -f docker-compose.windows.yml up
```

---

## Fotografije

Snimljene slike se spremaju u `photos/` folder na tvom računalu.

## Gašenje

```bash
docker compose down
```
