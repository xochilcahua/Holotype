# GitHub and publishing: a first-time guide

A repository is your project folder plus a record of saved changes. Git is the tool that keeps that record on your computer. GitHub stores a copy online. GitHub Pages serves the app's files to a browser.

## What the main terms mean

| Term | Meaning here |
| --- | --- |
| Repository, or repo | Holotype's source files and change history. |
| Commit | A saved snapshot with a short message explaining the change. |
| `main` | The branch holding the current version of the app. |
| `origin` | The name Git gives this project's GitHub address. |
| Push | Upload local commits to GitHub. |
| Pull | Bring changes from GitHub into your local copy. |
| Actions | Automated tasks; this project uses one to rebuild and publish the website. |
| Deployment | A version of the app made available at the website address. |

## First publication

The setup creates a public repository named Holotype, saves an initial commit and pushes it to `main`. Public means anyone can read the source. Your browser's ratings and personal session files are kept out of that upload.

Then GitHub Pages is enabled with **GitHub Actions** as its source. `.github/workflows/pages.yml` rebuilds the language bundle and portable app, checks the build in Chromium and publishes the website.

In GitHub, open the repository's **Actions** tab to follow the publishing run. A green check means the run completed; a red cross means a step failed. Select the run and a step to read its output.

The repository is at `https://github.com/xochilcahua/Holotype`. The app is usually at `https://xochilcahua.github.io/Holotype/`. Replace xochilcahua with the account used for setup. **Settings → Pages** shows the actual app address.

## Open it on your phone

Open the app address in Safari, Chrome or another browser. The page runs there without downloading the project or starting a local server.

To keep an icon on your phone, use Safari's Share menu and **Add to Home Screen** on iPhone, or Chrome's menu and its home-screen option on Android. The wording varies by browser. An icon does not make the app available offline; download `dist/Holotype.html` if you need a portable copy.

Your ratings remain in that browser. To move them between devices, save a session file, transfer it, and load it in the other browser. Clearing site data can remove local ratings, so save a file when you want a separate backup.

## Update through VS Code

Open the Holotype repository folder in VS Code and edit a file. For app wording, edit the second line of an entry in `copy/English` or `copy/Español`.

1. Save your files.
2. Open **Source Control** to see the changed files. Select one to compare before and after.
3. Stage the files you want to include with the **+** button.
4. Write a commit message, such as `Clarify the rating instructions`, and commit.
5. Choose **Push** or **Sync Changes** to send the commit to GitHub.
6. Follow the publishing run in GitHub's **Actions** tab, then refresh the app.

A commit saves the change locally. A push uploads it and triggers publishing. The website keeps its address between updates.

You can also edit text directly on GitHub: open a file, choose its edit button, make the change and commit to `main`. That triggers the same workflow. Pull those changes into VS Code before making your next local edit.

## Command-line equivalents

Run these in your local Holotype folder:

```sh
git status                    # list changed files
git diff                      # inspect changes
git add copy/English          # stage the wording you edited
git commit -m "Update English wording"
git push                      # upload and publish
git pull                      # bring down changes made on GitHub
```

When Python and browser-testing tools are installed, use the checks in [the README](../README.md) before pushing. GitHub also rebuilds and checks the portable app before it publishes.

## Find a problem

If the GitHub repository shows your latest commit but the website has not changed, check **Actions**. It may still be publishing, or a check may have failed. **Settings → Pages** should have **GitHub Actions** selected as its source.

If publishing finished successfully, reload the browser. Your existing ratings and chosen language can survive an app update; use Reset when you want a blank English session.

Read GitHub's [Pages workflow guide](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) for more about the hosting steps.
