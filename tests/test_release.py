import unittest

from blokus.release import (
    classify_release_areas,
    extract_bullets_under_heading,
    final_tag_from_rc,
    next_rc_tag,
)


class ReleaseHelpersTests(unittest.TestCase):
    def test_next_rc_tag_increments_highest_known_candidate(self) -> None:
        tag = next_rc_tag("0.1.0", ["v0.1.0-rc.1", "v0.1.0-rc.3", "v0.0.9-rc.2"])

        self.assertEqual(tag, "v0.1.0-rc.4")

    def test_final_tag_from_rc_strips_release_candidate_suffix(self) -> None:
        self.assertEqual(final_tag_from_rc("v0.1.0-rc.2"), "v0.1.0")
        self.assertEqual(final_tag_from_rc("v0.1.0"), "v0.1.0")

    def test_classify_release_areas_groups_expected_paths(self) -> None:
        areas = classify_release_areas(
            [
                "src/blokus/engine.py",
                "tests/test_engine.py",
                "fixtures/states/classic_initial.json",
                "docs/RELEASE_POLICY.md",
                ".github/workflows/release-candidate.yml",
                "scripts/package_release.sh",
            ]
        )

        self.assertEqual(areas, ("ci", "docs", "fixtures", "scripts", "source", "tests"))

    def test_extract_bullets_under_heading_reads_open_risks(self) -> None:
        markdown = """
# Requirements

## Open risks and open issues

- First risk
- Second risk

## Another heading

- Ignore me
""".strip()

        bullets = extract_bullets_under_heading(markdown, "Open risks and open issues")

        self.assertEqual(bullets, ("First risk", "Second risk"))


if __name__ == "__main__":
    unittest.main()
