# mrmonitor

Monitor your open MRs on Gitlab easily

## Usage

To list MRs from projects 1, 2 and 3 from user john.doe:

`python3 mrmonitor.py show 1,2,3 --user john.doe`

## Configuration

Mandatory environment variables are `GITLAB_URI` and `PRIVATE_TOKEN`.

You can also add them to your `.env` file in the project root directory.

### Jira issue parsing

If your MRs have a Jira ticket number in the title, you can optionally configure
a regex so mrmonitor will also display a Jira URL for the MR:

```
JIRA_URL=https://a.jira.instance.com/browse/
JIRA_REGEX=\[(SAMPLEPROJECT-\d+)\]
```

`JIRA_REGEX` is a comma separated list of regexes (multiple projects).
