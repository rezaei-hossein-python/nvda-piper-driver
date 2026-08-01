"""SCons gettext builders used by the official NVDA add-on template."""

from SCons.Action import Action


def exists(env) -> bool:
	return True


XGETTEXT_COMMON_ARGS = (
	"--msgid-bugs-address='$gettext_package_bugs_address' "
	"--package-name='$gettext_package_name' "
	"--package-version='$gettext_package_version' "
	"--keyword=pgettext:1c,2 -c -o $TARGET $SOURCES"
)


def generate(env) -> None:
	env.SetDefault(gettext_package_bugs_address="example@example.com")
	env.SetDefault(gettext_package_name="")
	env.SetDefault(gettext_package_version="")
	env["BUILDERS"]["gettextMoFile"] = env.Builder(
		action=Action("msgfmt -o $TARGET $SOURCE", "Compiling translation $SOURCE"),
		suffix=".mo",
		src_suffix=".po",
	)
	env["BUILDERS"]["gettextPotFile"] = env.Builder(
		action=Action("xgettext " + XGETTEXT_COMMON_ARGS, "Generating pot file $TARGET"),
		suffix=".pot",
	)
	env["BUILDERS"]["gettextMergePotFile"] = env.Builder(
		action=Action(
			"xgettext --omit-header --no-location " + XGETTEXT_COMMON_ARGS,
			"Generating pot file $TARGET",
		),
		suffix=".pot",
	)
