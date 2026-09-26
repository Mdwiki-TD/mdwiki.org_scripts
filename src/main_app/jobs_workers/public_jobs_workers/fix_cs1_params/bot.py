#!/usr/bin/python3
""" """

import logging
import wikitextparser as wtp

from .archive_date_maker import make_archive_date, make_archive_date_and_url

logger = logging.getLogger(__name__)

dup_args = {
    "trans-title": [
        "trans_title",
        "trans title",
        "transtitle",
    ],
    "dead-url": [
        "deadurl",
    ],
    "access-date": [
        "accessdate",
        "access date",
        "accessDate",
    ],
    "archive-date": [
        "archivedate",
        "archive date",
    ],
    "archive-url": [
        "archiveurl",
        "archive url",
    ],
    "chapter-url": [
        "chapterurl",
        "chapter url",
    ],
    "url-access": [
        "urlaccess",
        "url access",
    ],
    "author-link": [
        "authorlink",
        "author link",
    ],
    "editor-link": [
        "editorlink",
        "editor link",
    ],
}

old_to_new_params = {}

for new, old in dup_args.items():
    for x in old:
        old_to_new_params[x] = new

def gt_arg(temp, name: str):
    if temp.has_arg(name):
        va = temp.get_arg(name)
        if va and va.value and va.value.strip():
            return va.value.strip()
    return ""


class OnePageArchive:
    def __init__(self, title: str, text: str) -> None:
        self.title = title
        self.text = text
        self.summary = "Fix reference parameters "

        self.added = {}

    def run(self) -> str:
        newtext = self.fix_it(self.text)

        if self.text == newtext:
            return self.text

        added_str = ", ".join([f"{k}:{v}" for k, v in self.added.items()])

        if self.added:
            logger.info(f" >> {self.title} {added_str}")
            self.summary += f" (Add: {added_str})"
        return newtext

    def fix_it(self, text: str) -> str:
        parser = wtp.parse(text)
        for temp in parser.templates:
            temp_str = temp.string
            if not temp_str or temp_str.strip() == "":
                continue

            self.archive_param(temp)
            # temp.rm_dup_args_safe()

        return parser.string

    def archive_param(self, temp: wtp.Template) -> wtp.Template:

        url = gt_arg(temp, "url")
        archiveurl = gt_arg(temp, "archive-url")

        archive_date = gt_arg(temp, "archive-date") or gt_arg(temp, "archivedate")

        if archiveurl and not archive_date:
            archive_date = make_archive_date(archiveurl)

            if archive_date:
                temp.set_arg("archive-date", archive_date)

                self.param_added_plus("archive-date")


        chapterurl = gt_arg(temp, "chapter-url") or gt_arg(temp, "chapterurl")

        if not url and archiveurl and not chapterurl:
            found_it, archivedate, n_url, archiveurl = make_archive_date_and_url(archiveurl)

            if found_it:
                temp.set_arg("url", n_url)
                self.param_added_plus("url")

                if not archive_date:
                    temp.set_arg("archive-date", archivedate)
                    self.param_added_plus("archive-date")

        return temp

    def param_added_plus(self, param: str) -> None:
        self.added.setdefault(param, 0)
        self.added[param] += 1


class OnePage:
    def __init__(self, title, text) -> None:
        self.title = title
        self.text = text
        self.summary = "Fix reference parameters "
        self.replaced = {}
        self.removed = {}

    def run(self) -> str:
        newtext = self.fix_text(self.text)

        if self.text == newtext:
            return self.text

        if self.replaced:
            replace_str = ", ".join([f"{k}>{old_to_new_params.get(k, k)}({v})" for k, v in self.replaced.items()])
            logger.info(f" >> {self.title} {replace_str}")
            self.summary += f"(replace: {replace_str})"

        if self.removed:
            removed_str = ", ".join([f"{k}:{v}" for k, v in self.removed.items()])
            logger.info(f" >> {self.title} {removed_str}")

            self.summary += f" (remove: {removed_str})"

        return newtext

    def one_fix(self, temp: wtp.Template, old_p: str, new_p: str) -> None:
        if temp.has_arg(old_p) and temp.has_arg(new_p):

            p1_value = gt_arg(temp, old_p)
            p2_value = gt_arg(temp, new_p)

            if not p2_value:
                temp.set_arg(new_p, p1_value)

            if p1_value == p2_value:
                logger.info(f"<<yellow>> : {old_p} && {new_p} == <<green>> ({p1_value})")
            else:
                logger.info(f"<<yellow>> : |{old_p}={p1_value} && |{new_p}={p2_value}")

            logger.info(f"\t <<red>> del {old_p=}")

            self.removed.setdefault(old_p, 0)
            self.removed[old_p] += 1

            temp.del_arg(old_p)

    def fix_dupls(self, temp: wtp.Template) -> None:
        for new, old in dup_args.items():
            for x in old:
                self.one_fix(temp, x, new)

    def fix_text(self, text: str) -> str:

        parser = wtp.parse(text)

        for temp in parser.templates:

            temp_str = temp.string

            if not temp_str or temp_str.strip() == "":
                continue

            self.fix_dupls(temp)

            # temp.rm_dup_args_safe()

        for temp in parser.templates:

            temp_str = temp.string

            if not temp_str or temp_str.strip() == "":
                continue

            changed = False

            for arg in temp.arguments:

                if arg.name.strip() in old_to_new_params:

                    old_name = arg.name.strip()
                    new_name = old_to_new_params[arg.name.strip()]

                    self.replaced.setdefault(old_name, 0)
                    self.replaced[old_name] += 1

                    arg.name = new_name

                    changed = True
                    continue

                if "-" in arg.name.strip() and temp.has_arg(arg.name.strip().replace("-", "")):
                    arg.name = arg.name.strip().replace("-", "")
                    changed = True

            if changed:
                temp.rm_dup_args_safe()

        text = parser.string

        return text


__all__ = [
    "OnePageArchive",
    "OnePage",
    "gt_arg",
]
