This directory contains changelog entries: short files that contain a small
**MarkDown**-formatted text that will be added to ``CHANGELOG.md`` by `towncrier
<https://towncrier.readthedocs.io/en/latest/>`__.

The ``CHANGELOG.md`` will be read by **users**, so this description should be aimed to
urllib3 users instead of describing internal changes which are only relevant to the
developers.

Make sure to use full sentences in the **past tense** and use punctuation.

Each file should be named like ``<ISSUE>.<TYPE>.rst``, where ``<ISSUE>`` is an issue
number, and ``<TYPE>`` is one of those types:

* added
* changed
* fixed
* removed
* deprecated
* security

So for example: ``123.added.rst``, ``456.fixed.rst``.

If your pull request fixes an issue, use that number here. If there is no issue, then
after you submit the pull request and get the pull request number you can add a
changelog using that instead.

If your change does not deserve a changelog entry, apply the `Skip Changelog` GitHub
label to your pull request.