### Situation 1: Just Getting Started (Before you type a single line of code)

**Goal:** Ensure your local computer looks exactly like the GitHub server so you aren't working on old versions.

1.  **Open VS Code.**
2.  **Open the Terminal** (`Ctrl` + `` ` ``).
3.  **Run this command:**
    `bash
git pull origin main
` > **Why?** If a teammate fixed a bug 10 minutes ago, you want that fix on your machine _before_ you start working. **Never start working without pulling first.**

---

### Situation 2: Finishing Up (Uploading your work)

**Goal:** Save your changes and send them to the team.

**Step A: Save & Stage**

1.  Make sure all your files are saved (`Ctrl + S`).
2.  Run these commands in the terminal:
    ```bash
    git add .
    ```
    _(This tells Git: "I want to include all the files I changed.")_

**Step B: Commit**

1.  Wrap up your changes with a message:
    ```bash
    git commit -m "Description of what I fixed"
    ```
    _(Keep the message simple but clear, e.g., "Fixed login button" or "Updated homepage CSS".)_

**Step C: The "Safety" Pull (CRITICAL)**
Before you push, check if anyone else pushed code while you were working.

1.  Run:
    ```bash
    git pull origin main
    ```
2.  **If it says "Already up to date":** Great, proceed to Step D.
3.  **If it downloads files and auto-merges:** Great, proceed to Step D.
4.  **If it says "CONFLICT":** You MUST fix the files with red/green highlights in VS Code, save them, add them again (using command from Step A), and commit again (using command from Step B).

**Step D: Push**

1.  Send your code to GitHub:
    ```bash
    git push origin main
    ```

---

### ⚠️ Two Golden Rules for "Main Branch" Teams

1.  **The "I'm Pushing" Yell:** Before you push code, send a message to your group chat: _"I am pushing to main now."_ Wait for the confirmation that no one else is currently pushing.
2.  **Small Commits:** Do not work for 6 hours and try to push everything at once. Push small updates every hour. This reduces the chance of huge conflicts.
