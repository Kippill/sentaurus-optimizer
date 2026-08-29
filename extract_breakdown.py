import re
from pathlib import Path


LOG_FILE = Path("breakdown_console.log")


def main():
    text = LOG_FILE.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    pattern = re.compile(
        r"Maximum Field:\s*([0-9Ee+\-.]+)"
        r".*?"
        r"Ionization-Integrals:\s*"
        r"-+\s*"
        r"Electron:\s*([0-9Ee+\-.]+)\s*"
        r"Hole:\s*([0-9Ee+\-.]+)"
        r".*?"
        r"anode\s+([0-9Ee+\-.]+)",
        re.S,
    )

    rows = []

    for match in pattern.finditer(text):
        emax = float(match.group(1))
        phi_e = float(match.group(2))
        phi_h = float(match.group(3))
        voltage = float(match.group(4))

        rows.append(
            {
                "V": voltage,
                "phi_e": phi_e,
                "phi_h": phi_h,
                "phi_max": max(phi_e, phi_h),
                "Emax": emax,
            }
        )

    if not rows:
        raise RuntimeError("No ABA points found in log.")

    print()
    print("=" * 76)
    print("ABA BREAKDOWN EXTRACTION")
    print("=" * 76)

    print(
        f"{'V, V':>10} "
        f"{'Phi_e':>12} "
        f"{'Phi_h':>12} "
        f"{'Phi_max':>12} "
        f"{'Emax, V/cm':>15}"
    )

    for row in rows[-15:]:
        print(
            f"{row['V']:10.4f} "
            f"{row['phi_e']:12.6f} "
            f"{row['phi_h']:12.6f} "
            f"{row['phi_max']:12.6f} "
            f"{row['Emax']:15.6e}"
        )

    # Find first crossing Phi_max = 1
    for left, right in zip(rows[:-1], rows[1:]):
        p1 = left["phi_max"]
        p2 = right["phi_max"]

        if p1 < 1.0 <= p2:
            v1 = left["V"]
            v2 = right["V"]

            vbr = v1 + (1.0 - p1) * (v2 - v1) / (p2 - p1)

            emax = (
                left["Emax"]
                + (vbr - v1)
                * (right["Emax"] - left["Emax"])
                / (v2 - v1)
            )

            print()
            print("=" * 76)
            print("BREAKDOWN")
            print("=" * 76)

            print(f"Bracket: {v1:.6f} V -> {v2:.6f} V")
            print(f"Phi:     {p1:.6f} -> {p2:.6f}")
            print()
            print(f"Vbr ABA       = {vbr:.6f} V")
            print(f"|Vbr|         = {abs(vbr):.6f} V")
            print(f"Emax at Vbr   = {emax:.6e} V/cm")

            return

    print()
    print("Phi_max = 1 crossing was not found.")


if __name__ == "__main__":
    main()