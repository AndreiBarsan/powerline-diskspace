import re
import subprocess
from datetime import datetime
from typing import Optional, Mapping

from powerline import PowerlineLogger
from powerline.segments import Segment, with_docstring
from powerline.theme import requires_segment_info, requires_filesystem_watcher


def get_disk_usage() -> dict:
    """Returns disk usage in Linux as a list of dictionaries parsed from the output of 'df'."""
    # We use 'df' instead of 'os.statvfs' because we want to get ALL disk usages.
    linux_command = [
        "df",
        "--local",
        "--portability",
        "--print-type",
    ]
    result = subprocess.run(linux_command, stdout=subprocess.PIPE)
    output = result.stdout.decode("utf-8").split("\n")

    # Parse the output columns: filesystem, type, 1024-blocks, used, available, capacity, mounted on
    res = []
    for row in output[1:]:
        if not row:
            continue
        columns = row.split()
        res.append(
            {
                "filesystem": columns[0],
                "type": columns[1],
                "blocks": int(columns[2]),
                "used": int(columns[3]),
                "available": int(columns[4]),
                "total": int(columns[3]) + int(columns[4]),
                "capacity": float(columns[5].replace("%", "")),
                "mounted_on": columns[6],
            }
        )

    return res


def filter_disk_usage(disk_usage: dict, mount_ignore_pattern: str) -> dict:
    """Filter out disk usage based on the mount_ignore_pattern."""
    mount_ignore_re = re.compile(mount_ignore_pattern)
    return [
        disk for disk in disk_usage if not mount_ignore_re.match(disk["mounted_on"])
    ]


@requires_filesystem_watcher
@requires_segment_info
class CustomSegment(Segment):
    """A segment for displaying the diskspace. See `__call__` for argument docs.

    Relies on `df` under the hood, so it should work on most *nix systems. Requires Python 3.8+.

    Resources to learn about development:
      - https://www.ricalo.com/blog/custom-powerline-segment/#installing-the-package-in-editable-mode
    """

    last_df_call_time = None
    stat_cache = None

    def __call__(
        self,
        pl: PowerlineLogger,
        segment_info: Mapping,
        create_watcher,
        format: str,
        mount_ignore_pattern: str = "/snap|/dev|/run|/boot|/sys/fs",
        show_when_used_over_percent: Optional[Mapping[str, float]] = None,
        critical_threshold: Optional[float] = 90,
        update_rate_s: Optional[float] = 10.0,
    ) -> list:
        """Called by Powerline to render the segment.

        Args:
          pl: Powerline logger.
          segment_info: A dictionary with information about the segment.
          create_watcher: A function to create a filesystem watcher.
          format: A format string to render the segment. Valid placeholders are:
            - {filesystem}  - the filesystem name, e.g., /dev/sda1
            - {type}        - the type of the filesystem, e.g., ext4
            - {blocks}      - the total number of 1K blocks
            - {used}        - the number of used 1K blocks
            - {available}   - the number of available 1K blocks
            - {total}       - {used} + {available}
            - {capacity}    - percentage of occupied space, expressed as a float 0..100
            - {mounted_on}  - the mount point, e.g., /mnt/mydata
          mount_ignore_pattern: A regex pattern to ignore certain mounts, e.g., "/snap".
          show_when_used_over_percent: A dictionary with mount points and the percentage after which to show the
            capacity of that mount point. E.g., {"/": 80} will show the capacity of the root mount point if it is
            at or over 80% full. Missing mount points will always be shown.
          critical_threshold: The threshold at which to consider the disk usage critical (color red).
          update_rate_s: The rate at which to update the disk usage statistics. Note that Powerline may call this
            function more often than this rate, but the disk usage will only be updated at this rate.
        """
        del pl  # Unused.
        del segment_info  # Unused.
        del create_watcher  # Unused.
        if show_when_used_over_percent is None:
            show_when_used_over_percent = {"/": 80}

        # Cache the stats to avoid calling `df` too often.
        now = datetime.now()
        since_last_call = now - self.last_df_call_time if self.last_df_call_time else None
        if since_last_call is None or since_last_call.total_seconds() > update_rate_s:
            self.stat_cache = filter_disk_usage(get_disk_usage(), mount_ignore_pattern)

        stats = self.stat_cache
        chunks = []
        for stat in stats:
            if stat["mounted_on"] in show_when_used_over_percent:
                if stat["capacity"] < show_when_used_over_percent[stat["mounted_on"]]:
                    continue

            # See 'https://github.com/powerline/powerline/blob/develop/powerline/config_files/colorschemes/solarized.json'
            # for examples of common highlight groups.
            highlight_group = (
                "information:additional"
                if stat["capacity"] < critical_threshold
                else "critical:failure"
            )

            chunks.append(
                {
                    "contents": format.format(**stat),
                    "highlight_groups": [highlight_group],
                    "draw_inner_divider": True,
                }
            )

        return chunks


Diskspace = with_docstring(CustomSegment(), """Return a custom segment.""")


# TODO track the themes/tmux/... config in your dotfile repo.

if __name__ == "__main__":
    from pprint import pprint

    pprint(filter_disk_usage(get_disk_usage(), "/snap|/dev|/run|/boot|/sys/fs"))
