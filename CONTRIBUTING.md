# Contributing guidelines

First off, thank you for considering contributing.

**Please note, that by contributing to our project you agree to the DCO! [More info](#dco)**

## Why do these guidelines exists?

Following these guidelines helps to communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

## What to do

Lemming is an open source project and we love to receive contributions from our community! There are many ways to contribute, from improving the documentation, submitting bug reports and feature requests or writing code.

## Rules

- Fill issue templates.
- If you are making a big pull request, create an issue first.
- Read the [code of conduct](CODE_OF_CONDUCT.md).
- Search open **and closed** issues **and** pull requests.
- Please, **don't** open an issue for questions. Ask it in the discussions tab!
- Make sure to put an X to the square brackets at the end of the issue, if you read the contributing guidelines, and the code of conduct. **If you don't put an X into all of them, your issue will be closed!**
- Don't forget to add an entry to the changelog. Unless you know what you are doing, put it in the Unreleased section. For more information, see the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
- Please follow our [code style](https://github.com/koviubi56/koviubi56/blob/main/code_style.md).

## How to file a bug report?

1. Go to Lemming's GitHub repository.
1. Click on the `Issues` tab.
1. Click on the green `New issue` button.
1. Click on the green `Get started` button next to `Bug report`.
1. You now have to write the issue.
   1. Write a good title.
      Good: `ValueError when calling foo() with bar=False`
      Bad: `ValueError`
   1. Replace comments (`<!-- ... -->`) with text.
      Good: `A ValueError is raised, when foo() is called with bar=False.`
      Bad: `<!-- What is the bug? -->`
   1. Put `X` in the square brackets at the end of the issue.
      Good: `- [X] I agree to the [code of conduct](CODE_OF_CONDUCT.md)`
      Bad: `- [ ] I agree to the [code of conduct](CODE_OF_CONDUCT.md)`
1. Click on the green `Submit new issue` button.
1. Done! You now have to wait for the issue to be resolved. It's important, that you don't forget about the issue.

## How to suggest a feature?

1. Go to Lemming's GitHub repository.
1. Click on the `Issues` tab.
1. Click on the green `New issue` button.
1. Click on the green `Get started` button next to `Give an idea`.
1. You now have to write the issue.
   1. Write a good title.
      Good: `Add a progress bar`
      Bad: `Bar`
   1. Replace comments (`<!-- ... -->`) with text.
      Good: `A progress bar could be shown when foo() is called.`
      Bad: `<!-- What is the idea? What feature do you want? -->`
   1. Put `X` in the square brackets at the end of the issue.
      Good: `- [X] I agree to the [code of conduct](CODE_OF_CONDUCT.md)`
      Bad: `- [ ] I agree to the [code of conduct](CODE_OF_CONDUCT.md)`
1. Click on the green `Submit new issue` button.
1. Done! You now have to wait for the issue to be resolved. It's important, that you don't forget about the issue.

## How to set up your environment?

1. Clone the GitHub repository using `git clone`. _[Need more help?](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)_
1. Create a virtual environment using `venv venv`. _[Need more help?](https://packaging.python.org/en/latest/tutorials/installing-packages/#creating-virtual-environments)_
1. Activate the virtual environment: _[Need more help?](https://packaging.python.org/en/latest/tutorials/installing-packages/#tab-set--5-input--1)_
  **On PowerShell**: `.\\venv\\Scripts\\Activate.ps1`
  **On cmd.exe**: `.\\venv\\Scripts\\activate.bat`
  **On Bash**: `source ./venv/Scripts/activate`

### Install dependencies

Run `pip install -Ur requirements.txt`. _[Need more help?](https://packaging.python.org/en/latest/tutorials/installing-packages/#requirements-files)_

## Pull requests

- **Read, understand, and agree to the DCO. [More info](#dco)**
- Note the [Code of Conduct](CODE_OF_CONDUCT.md).
- Create an issue first.
- Wait until a maintainer accepts it.
- Create a fork.
- Create a **draft** pull request
- Make the changes
- Make the draft pull request ready to review (button)
- Request review
- Wait...

## Priority

### Small

- Spelling / grammar fixes
- Typo correction, white space and formatting changes
- Comment clean up
- Adding logging messages or debugging output

### Medium

- Bug fixes that fix errors that made a part of the program buggy/unusable.
- New features

### High

- Bug fixes that fix errors that made the whole program buggy/unusable.
- Security vulnerabilities

## Security vulnerabilities

In order to determine whether you are dealing with a security issue, ask yourself these two questions:

- Can I access something that's not mine, or something I shouldn't have access to?
- Can I disable something for other people?

If the answer to either of those two questions are "yes", then you're probably dealing with a security issue. _Note that even if you answer "no" to both questions, you may still be dealing with a security issue._

How to report them can be found in the [SECURITY.md](SECURITY.md) file.

## DCO

By contributing to our project you fully agree to the whole DCO.

By [signing off](https://git-scm.com/docs/git-commit#Documentation/git-commit.txt--s) your git commits you explicitly agree with the DCO.

A copy of the DCO can be found at <https://developercertificate.org/> or here:

> Developer Certificate of Origin
> Version 1.1
>
> Copyright (C) 2004, 2006 The Linux Foundation and its contributors.
>
> Everyone is permitted to copy and distribute verbatim copies of this
> license document, but changing it is not allowed.
>
> Developer's Certificate of Origin 1.1
>
> By making a contribution to this project, I certify that:
>
> (a) The contribution was created in whole or in part by me and I
> have the right to submit it under the open source license
> indicated in the file; or
>
> (b) The contribution is based upon previous work that, to the best
> of my knowledge, is covered under an appropriate open source
> license and I have the right under that license to submit that
> work with modifications, whether created in whole or in part
> by me, under the same open source license (unless I am
> permitted to submit under a different license), as indicated
> in the file; or
>
> (c) The contribution was provided directly to me by some other
> person who certified (a), (b) or (c) and I have not modified
> it.
>
> (d) I understand and agree that this project and the contribution
> are public and that a record of the contribution (including all
> personal information I submit with it, including my sign-off) is
> maintained indefinitely and may be redistributed consistent with
> this project or the open source license(s) involved.

Any contribution submitted for inclusion in the project by you, shall be licensed under the project's license, without any additional terms or conditions.
