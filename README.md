# LogFileTools
Utilities for processing Logiscend Log files

```
taglogparser.py [-a|-A] [-r|-R] [-c|-C] [-d] [-g] [-z <ServerHost.zip>] [-g <gateway ip of interest>] [-t <tag uid>] [-o <outputfile>])
-a = report tag gateway affiliation for failed tag commands
-A = report tag gateway affiliation for all tags
-z = use zip file of logs and report on all files contained within.
-t = focus on this tag
-R = report RSSI status for all tags.
-r = report RSSI status for only failed tags
-C = report all tag commands failures
-c = report only failed tag commands
-d = report only tags with command retries
-G = Report a list of tags that have affiliated with each gateway
```
