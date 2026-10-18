-- Harness for olink.yazi/main.lua: executes the plugin with stubbed
-- yazi globals and live-captured `olink` output. No yazi binary or fzf needed.
--
-- Knobs (set by the driver before executing this file):
--   PLUGIN_PATH : path to the plugin file under test
--   CANNED_PATH : path to a file returning { list = "...", urls = { name = url } }
--   CWD         : directory yazi is "browsing"
--   WHICH_IDX   : 1-based pick in the which-key menu, or nil for cancel
--   CONFIRM     : boolean, the confirm dialog answer
--   COPY        : boolean, mirrors `plugin olink --copy`
--   FAIL_LIST   : boolean, makes `olink list` fail
--   TEST_EXISTS : callable(path) -> boolean, injected by the driver
-- Observations land in flat OBS fields (nil when the call never happened):
--   n_cands, first_desc, emit_cmd, clip, notify_content, notify_level,
--   confirm_shown, confirm_body.

cx = { active = { current = { cwd = CWD } } }

local function make_url(p)
	local u = { _p = p }
	setmetatable(u, {
		__tostring = function(self)
			return self._p
		end,
	})
	function u:join(name)
		-- Native separator like yazi's own Url.join, so mixed trees resolve.
		local sep = self._p:find("\\", 1, true) and "\\" or "/"
		return make_url(self._p .. sep .. name)
	end
	-- Both separators, mirroring yazi's own Url.parent on Windows.
	local parent_p = p:match("^(.*)[/\\][^/\\]+$")
	if parent_p == "" then
		parent_p = nil
	end
	u.parent = parent_p and make_url(parent_p) or nil
	return u
end

Url = function(p)
	return make_url(p)
end

fs = {
	cha = function(url)
		if TEST_EXISTS(tostring(url)) then
			return {}, nil
		end
		return nil, "missing"
	end,
}

local CANNED = dofile(CANNED_PATH)

-- Set once the first stubbed `olink list` fails; lets one scenario fail
-- over then recover so the ancestor retry is exercised.
local failed_once = false

-- Same for a successful-but-empty list, the other retry trigger.
local emptied_once = false

Command = setmetatable({ PIPED = {}, NULL = {}, INHERIT = {} }, {
	__call = function(_, prog)
		local c = { _prog = prog, _args = {} }
	function c:arg(a)
		if type(a) == "table" then
			for _, v in ipairs(a) do
				self._args[#self._args + 1] = v
			end
		else
			self._args[#self._args + 1] = a
		end
		return self
	end
	function c:stdin(_stdio)
		return self
	end
	function c:stdout(_stdio)
		return self
	end
	function c:output()
		assert(self._prog == "olink", "unexpected program: " .. tostring(self._prog))
		if self._args[1] == "list" then
			if FAIL_LIST or (FAIL_FIRST and not failed_once) then
				failed_once = true
				return { status = { success = false, code = 5 }, stdout = "", stderr = "Error: boom" }, nil
			end
			if EMPTY_FIRST and not emptied_once then
				emptied_once = true
				return { status = { success = true, code = 0 }, stdout = "No targets available for this project.\n", stderr = "" }, nil
			end
			return { status = { success = true, code = 0 }, stdout = CANNED.list, stderr = "" }, nil
		elseif self._args[1] == "url" then
			local url = CANNED.urls[self._args[2]]
			assert(url ~= nil, "no canned url for: " .. tostring(self._args[2]))
			return { status = { success = true, code = 0 }, stdout = url .. "\n", stderr = "" }, nil
		end
		error("unexpected olink args")
	end
	-- (no spawn stub: the plugin never spawns subprocesses)
		return c
	end,
})

OBS = {}

ya = {
	sync = function(f)
		return function(...)
			return f(...)
		end
	end,
	which = function(opts)
		OBS.n_cands = #opts.cands
		OBS.first_desc = opts.cands[1] and opts.cands[1].desc or nil
		return WHICH_IDX
	end,
	confirm = function(opts)
		OBS.confirm_shown = true
		OBS.confirm_body = opts.body
		return CONFIRM
	end,
	emit = function(action, args)
		OBS.emit_cmd = args[1]
	end,
	notify = function(opts)
		OBS.notify_content = opts.content
		OBS.notify_level = opts.level
	end,
	clipboard = function(text)
		OBS.clip = text
	end,
	quote = function(s)
		return "'" .. s .. "'"
	end,
}

local plugin = dofile(PLUGIN_PATH)
plugin.entry({}, { args = { copy = COPY } })
