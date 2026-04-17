import pytest
from src.preprocess import split_diff_by_file, split_file_by_hunks

def test_split_diff_by_file():
    diff = """diff --git a/user.ts b/user.ts
--- a/user.ts
+++ b/user.ts
@@ -1,5 +1,6 @@
 def foo():
     return 1
+    return 2
diff --git a/utils.ts b/utils.ts
--- a/utils.ts
+++ b/utils.ts
@@ -1,3 +1,4 @@
 def bar():
     return 3
+    return 4
"""
    files = list(split_diff_by_file(diff))
    assert len(files) == 2
    assert files[0]["filename"] == "user.ts"
    assert files[1]["filename"] == "utils.ts"

def test_classify_file_type():
    from src.preprocess import classify_file_type
    assert classify_file_type("user.ts") == "backend"
    assert classify_file_type("User.tsx") == "frontend"
    assert classify_file_type("user.test.ts") == "test"
    assert classify_file_type("config.json") == "config"