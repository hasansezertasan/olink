-- ~/.config/yazi/plugins/olink.yazi/main.lua
--
-- Open olink targets (PyPI page, issues, CI, download stats, ...) for the
-- project you are browsing, without leaving yazi.
-- Requires the `olink` CLI on PATH (https://github.com/hasansezertasan/olink).
-- Picks with the which-key menu, then confirms with the full description
-- and resolved URL. Everything stays inside yazi's own UI.

--- Files that mark a project root. Kept in sync with what olink reads
--- (git remotes plus the per-ecosystem package manifests).
local MARKERS = {
	".git",
	"pyproject.toml",
	"package.json",
	"Cargo.toml",
	"go.mod",
	"composer.json",
	"pubspec.yaml",
	"pom.xml",
	"mix.exs",
}

--- One keystroke per target in the which-key menu (the fzf fallback).
local KEY_POOL = "abcdefghijklmnopqrstuvwxyz0123456789"

--- Current tab's cwd; `cx` is only readable from a sync context.
local get_cwd = ya.sync(function()
	return tostring(cx.active.current.cwd)
end)

local function exists(url)
	local cha, _ = fs.cha(url)
	return cha ~= nil
end

--- olink only works from the project root, so walk up from `start`
--- until a directory carries a known marker. (`parent` is yazi's own
--- Url property, so separators are correct on every platform.)
local function find_root(start)
	local url = Url(start)
	for _ = 1, 20 do
		for _, marker in ipairs(MARKERS) do
			if exists(url:join(marker)) then
				return tostring(url)
			end
		end
		local parent = url.parent
		if parent == nil or tostring(parent) == tostring(url) then
			return nil
		end
		url = parent
	end
	return nil
end

--- Run olink and return trimmed stdout, or nil plus an error message.
local function olink(args)
	local output, err = Command("olink"):arg(args):output()
	if output == nil then
		return nil, string.format("failed to start `olink`: %s", tostring(err))
	end
	if not output.status.success then
		local msg = output.stderr
		if msg == nil or msg == "" then
			msg = "olink exited with code " .. tostring(output.status.code)
		end
		return nil, msg
	end
	return (output.stdout:gsub("%s+$", "")), nil
end

--- Parse the human-readable `olink list` output into { name, desc } rows.
--- Each row looks like: `  pypi             - Open PyPI page`
local function parse_list(text)
	local rows = {}
	for line in text:gmatch("[^\r\n]+") do
		local name, desc = line:match("^%s+(%S+)%s+%-%s+(.+)$")
		if name ~= nil and desc ~= nil then
			rows[#rows + 1] = { name = name, desc = desc }
		end
	end
	return rows
end

local function fail(message)
	ya.notify({ title = "olink", content = message, level = "error", timeout = 5 })
end

--- Pick a target row with the which-key menu. Labels are names only: the
--- menu lays candidates out in columns, so each cell only fits a couple
--- dozen characters — names always fit, descriptions would chop mid-word.
--- The full description is shown on the confirm dialog instead.
--- Returns the row, or nil when dismissed.
local function pick_row(rows)
	local cands = {}
	for i, row in ipairs(rows) do
		if i > #KEY_POOL then
			break
		end
		cands[i] = { on = KEY_POOL:sub(i, i), desc = row.name }
	end

	local idx = ya.which({ cands = cands })
	if idx == nil then
		return nil
	end
	return rows[idx]
end

local function entry(self, job)
	local root = find_root(get_cwd())
	if root == nil then
		fail("no project root found above the current directory")
		return
	end

	local text, err = olink({ "list", "-d", root })
	if text == nil then
		fail(err)
		return
	end

	local rows = parse_list(text)
	if #rows == 0 then
		fail("no olink targets available for " .. root)
		return
	end

	local picked = pick_row(rows)
	if picked == nil then
		return
	end

	local url, uerr = olink({ "url", picked.name, "-d", root })
	if url == nil then
		fail(uerr)
		return
	end

	if job.args.copy then
		ya.clipboard(url)
		ya.notify({ title = "olink", content = "copied: " .. url, timeout = 3 })
		return
	end

	local open_it = ya.confirm({
		pos = { "center", w = 70, h = 10 },
		title = picked.name,
		body = picked.desc .. "\n" .. url,
	})
	if open_it then
		ya.emit("shell", { string.format("olink open %s -d %s", ya.quote(picked.name), ya.quote(root)) })
	end
end

return { entry = entry }
