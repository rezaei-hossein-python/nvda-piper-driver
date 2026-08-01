"""SCons builders for NVDA add-on manifests, documentation, and archives."""

from SCons.Script import Builder, Environment

from .addon import createAddonBundleFromPath
from .docs import md2html
from .manifests import generateManifest, generateTranslatedManifest


def generate(env: Environment) -> None:
	env.SetDefault(excludePatterns=tuple())
	addonAction = env.Action(
		lambda target, source, env: createAddonBundleFromPath(
			source[0].abspath,
			target[0].abspath,
			env["excludePatterns"],
		)
		and None,
		lambda target, source, env: f"Generating add-on {target[0]}",
	)
	env["BUILDERS"]["NVDAAddon"] = Builder(action=addonAction, suffix=".nvda-addon", src_suffix="/")

	env.SetDefault(brailleTables={})
	env.SetDefault(symbolDictionaries={})
	env.SetDefault(speechDictionaries={})

	manifestAction = env.Action(
		lambda target, source, env: generateManifest(
			source[0].abspath,
			target[0].abspath,
			addon_info=env["addon_info"],
			brailleTables=env["brailleTables"],
			symbolDictionaries=env["symbolDictionaries"],
			speechDictionaries=env["speechDictionaries"],
		)
		and None,
		lambda target, source, env: f"Generating manifest {target[0]}",
	)
	env["BUILDERS"]["NVDAManifest"] = Builder(action=manifestAction, suffix=".ini", src_suffix=".ini.tpl")

	translatedManifestAction = env.Action(
		lambda target, source, env: generateTranslatedManifest(
			source[1].abspath,
			target[0].abspath,
			mo=source[0].abspath,
			addon_info=env["addon_info"],
			brailleTables=env["brailleTables"],
			symbolDictionaries=env["symbolDictionaries"],
			speechDictionaries=env["speechDictionaries"],
		)
		and None,
		lambda target, source, env: f"Generating translated manifest {target[0]}",
	)
	env["BUILDERS"]["NVDATranslatedManifest"] = Builder(
		action=translatedManifestAction,
		suffix=".ini",
		src_suffix=".ini.tpl",
	)

	env.SetDefault(mdExtensions=[])
	markdownAction = env.Action(
		lambda target, source, env: md2html(
			source[0].path,
			target[0].path,
			moFile=env["moFile"].path if env["moFile"] else None,
			mdExtensions=env["mdExtensions"],
			addon_info=env["addon_info"],
		)
		and None,
		lambda target, source, env: f"Generating {target[0]}",
	)
	env["BUILDERS"]["md2html"] = env.Builder(action=markdownAction, suffix=".html", src_suffix=".md")


def exists() -> bool:
	return True
