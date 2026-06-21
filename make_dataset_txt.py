from pathlib import Path
import argparse

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def is_image(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in IMAGE_EXTS

def find_gt_for_input(input_img: Path, input_dir: Path, gt_dir: Path):
    """
    First tries matching exact relative filename.
    If not found, tries same stem with any image extension.
    """
    rel = input_img.relative_to(input_dir)
    exact = gt_dir / rel
    if exact.exists():
        return exact

    candidates = list((gt_dir / rel.parent).glob(input_img.stem + ".*"))
    candidates = [p for p in candidates if is_image(p)]
    if candidates:
        return candidates[0]

    return None

def collect_pairs(root: Path):
    """
    Finds folders like:
      root/something/input/
      root/something/gt/

    Returns lines like:
      something/input/image.jpg
    because your TransWeather loader builds:
      train_data_dir + input_name
    """
    root = root.resolve()
    grouped = {}
    all_lines = []

    for input_dir in sorted(root.rglob("input")):
        if not input_dir.is_dir():
            continue

        pair_dir = input_dir.parent
        gt_dir = pair_dir / "gt"

        if not gt_dir.exists():
            print(f"Skipping {input_dir}: no sibling gt/ folder")
            continue

        subset_name = pair_dir.relative_to(root).as_posix()
        lines = []

        for input_img in sorted(input_dir.rglob("*")):
            if not is_image(input_img):
                continue

            gt_img = find_gt_for_input(input_img, input_dir, gt_dir)
            if gt_img is None:
                print(f"Missing GT for: {input_img.relative_to(root)}")
                continue

            line = input_img.relative_to(root).as_posix()
            lines.append(line)

        if lines:
            grouped[subset_name] = lines
            all_lines.extend(lines)

    return grouped, sorted(all_lines)

def write_txt(path: Path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""))
    print(f"Wrote {len(lines):5d} lines -> {path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-root", default="data/train")
    parser.add_argument("--test-root", default="data/test")
    parser.add_argument("--train-out", default="data/train/all_generated.txt")
    parser.add_argument("--test-out", default="data/test/all_generated.txt")
    parser.add_argument(
        "--per-folder",
        action="store_true",
        help="Also create txt files like data/train/1977.txt and data/test/allfilter.txt",
    )
    args = parser.parse_args()

    for split_name, root_str, out_str in [
        ("train", args.train_root, args.train_out),
        ("test", args.test_root, args.test_out),
    ]:
        root = Path(root_str)
        out = Path(out_str)

        if not root.exists():
            print(f"Skipping {split_name}: {root} does not exist")
            continue

        grouped, all_lines = collect_pairs(root)

        print(f"\n[{split_name}] found {len(all_lines)} valid input/gt pairs")
        write_txt(out, all_lines)

        if args.per_folder:
            for subset_name, lines in grouped.items():
                # e.g. data/train/1977.txt or data/test/allfilter.txt
                subset_txt = root / f"{Path(subset_name).name}.txt"
                write_txt(subset_txt, lines)

if __name__ == "__main__":
    main()
