import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


class ReleaseWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.source = WORKFLOW.read_text(encoding="utf-8")
        self.workflow = yaml.safe_load(self.source)
        self.images = self.workflow["jobs"]["images"]

    def test_image_publication_waits_for_validated_archive_on_version_tags(self):
        self.assertEqual(self.images["needs"], "archive")
        self.assertIn("refs/tags/", self.images["if"])
        self.assertEqual(self.images["permissions"]["packages"], "write")
        self.assertEqual(self.images["permissions"]["id-token"], "write")
        self.assertEqual(self.images["permissions"]["attestations"], "write")

    def test_container_actions_are_pinned_to_full_commit_shas(self):
        docker_actions = re.findall(
            r"uses: (docker/[^@\s]+)@([0-9a-f]+)", self.source
        )
        self.assertEqual(len(docker_actions), 4)
        for action, revision in docker_actions:
            self.assertTrue(action)
            self.assertEqual(len(revision), 40)

    def test_both_images_publish_sbom_provenance_and_digest_attestations(self):
        steps = self.images["steps"]
        builds = [
            step
            for step in steps
            if step.get("uses", "").startswith("docker/build-push-action@")
        ]
        attestations = [
            step
            for step in steps
            if step.get("uses", "").startswith(
                "actions/attest-build-provenance@"
            )
        ]
        self.assertEqual(len(builds), 2)
        self.assertEqual(len(attestations), 2)
        for build in builds:
            self.assertIs(build["with"]["push"], True)
            self.assertIs(build["with"]["sbom"], True)
            self.assertEqual(build["with"]["provenance"], "mode=max")
            self.assertNotIn(":latest", build["with"]["tags"])
        for attestation in attestations:
            self.assertIn("outputs.digest", attestation["with"]["subject-digest"])
            self.assertIs(attestation["with"]["push-to-registry"], True)

    def test_both_dockerfiles_record_the_source_revision(self):
        for relative in ("Dockerfile", "dashboard/Dockerfile"):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("ARG VCS_REF=unknown", source)
            self.assertIn("org.opencontainers.image.revision=$VCS_REF", source)


if __name__ == "__main__":
    unittest.main()
