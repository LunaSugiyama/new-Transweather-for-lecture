from pathlib import Path
import shutil

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

repo = Path(".").resolve()

# Change this if you only want to clean one file, e.g.
# txt_files = [Path("data/train/allweather.txt")]
txt_files = sorted(Path("data").rglob("*.txt"))

def candidate_paths(token: str, txt_path: Path):
    token = token.strip()
    p = Path(token)

    candidates = []

    # Absolute path
    if p.is_absolute():
        candidates.append(p)

    # Relative to the txt file directory
    candidates.append(txt_path.parent / p)

    # Relative to repo root
    candidates.append(repo / p)

    # Relative to data/train or data/test
    parts = txt_path.parts
    if "train" in parts:
        candidates.append(repo / "data" / "train" / p)
    if "test" in parts:
        candidates.append(repo / "data" / "test" / p)

    return candidates

def token_is_image(token: str):
    token = token.strip().strip(",")
    return Path(token).suffix.lower() in IMAGE_EXTS

total_removed = 0

for txt_path in txt_files:
    txt_path = txt_path.resolve()
    lines = txt_path.read_text(errors="ignore").splitlines()

    kept = []
    removed = []

    for line in lines:
        stripped = line.strip()

        # Keep blank/comment lines
        if not stripped or stripped.startswith("#"):
            kept.append(line)
            continue

        tokens = stripped.replace(",", " ").split()
        image_tokens = [t.strip(",") for t in tokens if token_is_image(t)]

        # If the line has no image-looking token, keep it
        if not image_tokens:
            kept.append(line)
            continue

        missing = []
        for tok in image_tokens:
            if not any(c.exists() for c in candidate_paths(tok, txt_path)):
                missing.append(tok)

        if missing:
            removed.append((line, missing))
        else:
            kept.append(line)

    if removed:
        backup = txt_path.with_suffix(txt_path.suffix + ".bak")
        shutil.copy2(txt_path, backup)

        txt_path.write_text("\n".join(kept) + ("\n" if kept else ""))

        print(f"\nCleaned: {txt_path.relative_to(repo)}")
        print(f"Backup : {backup.relative_to(repo)}")
        print(f"Removed {len(removed)} lines")
        for line, missing in removed[:10]:
            print("  missing:", ", ".join(missing))
            print("  line   :", line)
        if len(removed) > 10:
            print(f"  ... and {len(removed) - 10} more")

        total_removed += len(removed)

print(f"\nDone. Total removed lines: {total_removed}")
