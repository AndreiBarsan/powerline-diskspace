# Powerline Disk Utilization Indicator

A tiny [Powerline](https://github.com/powerline/powerline) segment I wrote for `tmux` to show me disk space utilization in its status line.

Here is a screenshot of this segment in action:

![disk utilization example](doc/img/powerline-diskspace-screenshot.png)

The root `/` is red because, unlike `/cache`, it's over the `critical_threshold` I set to 40% for this example.

In this case, the relevant part of the powerline config (`cat ~/.config/powerline/themes/tmux/default.json`) is:

```
{
        "segments": {
                "right": [
                        {
                                "function": "powerline_diskspace.diskspace.Diskspace",
                                "priority": 30,
                                "args": {
                                        "format": "{mounted_on} @ {capacity:.0f}%",
                                        "mount_ignore_pattern": "(/snap|/dev|/run|/boot|/sys/fs)",
                                        "show_when_used_over_percent": {
                                                "/": 20,
                                        },
                                        "critical_threshold": 40
                                }
                        }
                ]
        }
}
```

(Other plug-ins like `uptime`, which are built into `tmux` are not shown.)

## Getting Started

System requirements:
 * Linux (macOS support is only partial)
 * Python 3.8+

Installation steps:

1. Install the Python package: `pip install powerline-diskspace`.
2. Update your `powerline` (not `tmux`!) config following the example above.
3. Restart the Powerline daemon: `powerline-daemon --replace`

If you have any questions or encounter issues setting up, please don't hesitate to open up an issue on GitHub!