import unittest
import tempfile
from pathlib import Path
from tools.kmp_scaffolder import KMPProjectScaffolder

class TestKMPScaffolder(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.test_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_scaffold_files_generation(self):
        KMPProjectScaffolder.scaffold(
            root_dir=str(self.test_dir),
            app_name="MyTestApp",
            package_name="com.test.app"
        )

        self.assertTrue((self.test_dir / "gradle/libs.versions.toml").exists())
        self.assertTrue((self.test_dir / "settings.gradle.kts").exists())
        self.assertTrue((self.test_dir / "build.gradle.kts").exists())
        self.assertTrue((self.test_dir / "composeApp/build.gradle.kts").exists())
        self.assertTrue((self.test_dir / "composeApp/src/commonMain/kotlin/com/test/app/App.kt").exists())
        self.assertTrue((self.test_dir / "composeApp/src/androidMain/kotlin/com/test/app/MainActivity.kt").exists())
        self.assertTrue((self.test_dir / "composeApp/src/iosMain/kotlin/com/test/app/MainViewController.kt").exists())
        self.assertTrue((self.test_dir / "composeApp/src/desktopMain/kotlin/com/test/app/main.kt").exists())
        self.assertTrue((self.test_dir / "composeApp/src/wasmJsMain/kotlin/com/test/app/main.kt").exists())

if __name__ == "__main__":
    unittest.main()
