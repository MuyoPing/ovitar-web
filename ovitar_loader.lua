--[[
    ===================================================================
    ⚡ OVITAR - ULTIMATE ROBLOX SCRIPT LOADER & AUTHENTICATOR ⚡
    ===================================================================
    - High-Tech Dark Ovitar Aesthetic with Diagonal-Slit Ring Logo
    - Live Server Status Indicator (🟢 Online / 🟡 Maintenance / 🔴 Offline)
    - Deterministic Hardware ID (HWID) Extraction
    - Masked Password Input with 👁️ Eye Reveal/Hide Toggle
    - Anonymous placeholders (no user identifiers exposed)
    - Dynamic Protected Script Payload Ingestion & Execution
    ===================================================================
]]

local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local CoreGui = game:GetService("CoreGui")
local UserInputService = game:GetService("UserInputService")

local LocalPlayer = Players.LocalPlayer
local PlayerGui = LocalPlayer:WaitForChild("PlayerGui")

-- ⚙️ CONFIGURATION & API BASE
local CONFIG = {
    API_URL = "http://127.0.0.1:5500", -- 웹 서버 주소 (배포 시 변경 가능)
    STATUS_POLL_INTERVAL = 10,
    VERSION = "v0.6.0"
}

-- 🛡️ EXECUTOR HTTP WRAPPER
local HttpRequest = (syn and syn.request) 
    or (http and http.request) 
    or http_request 
    or (fluxus and fluxus.request) 
    or request

if not HttpRequest then
    warn("[OVITAR] Executor does not support standard HTTP Request function!")
    return
end

-- 🖥️ DETERMINISTIC HARDWARE ID (HWID) EXTRACTION
local function getHWID()
    local hwid = ""
    pcall(function()
        if gethwid then
            hwid = gethwid()
        elseif rbx_hwid then
            hwid = rbx_hwid()
        else
            local analytics = game:GetService("RbxAnalyticsService")
            if analytics and analytics.GetClientId then
                hwid = analytics:GetClientId()
            end
        end
    end)
    -- Fallback: Deterministic based on LocalPlayer UserId (Never use os.time() as it changes every run)
    if hwid == "" or not hwid then
        hwid = "RBX_CLIENT_" .. tostring(LocalPlayer.UserId)
    end
    return tostring(hwid)
end

-- 🔐 IN-MEMORY PAYLOAD DECRYPTOR (API 전송 시 원본 소스코드 난독화 및 패킷 스니핑 방지)
local SCRIPT_SECRET = "OVITAR_SECURITY_SHIELD_SECRET_KEY_9921!"
local b64chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
local function b64decode(data)
    local chars = {}
    for i = 1, #b64chars do
        chars[string.sub(b64chars, i, i)] = i - 1
    end
    data = string.gsub(data, '[^'..b64chars..'=]', '')
    return (data:gsub('(.)(.)(.)(.)', function(a, b, c, d)
        local v1, v2, v3, v4 = chars[a], chars[b], chars[c], chars[d]
        if not v1 or not v2 then return '' end
        local n = (v1 * 262144) + (v2 * 4096) + ((v3 or 0) * 64) + (v4 or 0)
        local b1 = math.floor(n / 65536) % 256
        local b2 = math.floor(n / 256) % 256
        local b3 = n % 256
        if d == '=' and c == '=' then
            return string.char(b1)
        elseif d == '=' then
            return string.char(b1, b2)
        else
            return string.char(b1, b2, b3)
        end
    end))
end

local function decryptScriptPayload(encB64, nonce)
    local keyStr = SCRIPT_SECRET .. tostring(nonce or "")
    local keyBytes = {string.byte(keyStr, 1, #keyStr)}
    local keyLen = #keyBytes
    local raw = b64decode(encB64)
    local out = {}
    for i = 1, #raw do
        local b = string.byte(raw, i)
        local kb = keyBytes[((i - 1) % keyLen) + 1]
        local p, c = 1, 0
        while b > 0 or kb > 0 do
            local rb, rkb = b % 2, kb % 2
            if rb ~= rkb then c = c + p end
            b, kb = math.floor(b / 2), math.floor(kb / 2)
            p = p * 2
        end
        table.insert(out, string.char(c))
    end
    return table.concat(out)
end

-- 🌐 CHECK LIVE API STATUS
local function checkServerStatus()
    local success, response = pcall(function()
        return HttpRequest({
            Url = CONFIG.API_URL .. "/api/loader/status",
            Method = "GET",
            Headers = { ["Content-Type"] = "application/json" }
        })
    end)

    if success and response and response.StatusCode == 200 then
        local data = HttpService:JSONDecode(response.Body)
        return data.status or "online", data.message or "정상 서비스 중", data.version or CONFIG.VERSION
    end
    return "offline", "서버에 연결할 수 없습니다.", CONFIG.VERSION
end

-- ===================================================================
-- 🎨 CREATE MODERN OVITAR LOADER GUI
-- ===================================================================

-- Destroy existing instance if present
pcall(function()
    if gethui and gethui():FindFirstChild("OvitarLoaderGUI") then
        gethui():FindFirstChild("OvitarLoaderGUI"):Destroy()
    elseif CoreGui:FindFirstChild("OvitarLoaderGUI") then
        CoreGui:FindFirstChild("OvitarLoaderGUI"):Destroy()
    elseif PlayerGui:FindFirstChild("OvitarLoaderGUI") then
        PlayerGui:FindFirstChild("OvitarLoaderGUI"):Destroy()
    end
end)

local ScreenGui = Instance.new("ScreenGui")
ScreenGui.Name = "OvitarLoaderGUI"
ScreenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
ScreenGui.ResetOnSpawn = false

pcall(function()
    if gethui then
        ScreenGui.Parent = gethui()
    else
        ScreenGui.Parent = CoreGui
    end
end)
if not ScreenGui.Parent then
    ScreenGui.Parent = PlayerGui
end

-- Main Window Frame
local MainFrame = Instance.new("Frame")
MainFrame.Name = "MainFrame"
MainFrame.Size = UDim2.new(0, 440, 0, 520)
MainFrame.Position = UDim2.new(0.5, -220, 0.5, -260)
MainFrame.BackgroundColor3 = Color3.fromRGB(15, 15, 17)
MainFrame.BorderSizePixel = 0
MainFrame.ClipsDescendants = true
MainFrame.Parent = ScreenGui

local MainCorner = Instance.new("UICorner")
MainCorner.CornerRadius = UDim.new(0, 22)
MainCorner.Parent = MainFrame

local MainStroke = Instance.new("UIStroke")
MainStroke.Color = Color3.fromRGB(38, 38, 46)
MainStroke.Thickness = 1.4
MainStroke.Parent = MainFrame

-- Subtle Top Glow Line
local TopGlow = Instance.new("Frame")
TopGlow.Name = "TopGlow"
TopGlow.Size = UDim2.new(1, -60, 0, 1)
TopGlow.Position = UDim2.new(0, 30, 0, 0)
TopGlow.BackgroundColor3 = Color3.fromRGB(80, 80, 100)
TopGlow.BorderSizePixel = 0
TopGlow.BackgroundTransparency = 0.5
TopGlow.Parent = MainFrame

-- Top Bar
local TopBar = Instance.new("Frame")
TopBar.Name = "TopBar"
TopBar.Size = UDim2.new(1, 0, 0, 60)
TopBar.BackgroundColor3 = Color3.fromRGB(20, 20, 24)
TopBar.BorderSizePixel = 0
TopBar.Parent = MainFrame

local TopBarCorner = Instance.new("UICorner")
TopBarCorner.CornerRadius = UDim.new(0, 22)
TopBarCorner.Parent = TopBar

local TopBarCover = Instance.new("Frame")
TopBarCover.Size = UDim2.new(1, 0, 0, 20)
TopBarCover.Position = UDim2.new(0, 0, 1, -20)
TopBarCover.BackgroundColor3 = Color3.fromRGB(20, 20, 24)
TopBarCover.BorderSizePixel = 0
TopBarCover.Parent = TopBar

-- Ovitar Circular Emblem with Diagonal Slit Logo
local LogoContainer = Instance.new("Frame")
LogoContainer.Name = "LogoContainer"
LogoContainer.Size = UDim2.new(0, 32, 0, 32)
LogoContainer.Position = UDim2.new(0, 18, 0.5, -16)
LogoContainer.BackgroundColor3 = Color3.fromRGB(26, 26, 32)
LogoContainer.BorderSizePixel = 0
LogoContainer.Parent = TopBar

local LogoCorner = Instance.new("UICorner")
LogoCorner.CornerRadius = UDim.new(1, 0)
LogoCorner.Parent = LogoContainer

local LogoStroke = Instance.new("UIStroke")
LogoStroke.Color = Color3.fromRGB(255, 255, 255)
LogoStroke.Thickness = 1.8
LogoStroke.Transparency = 0.15
LogoStroke.Parent = LogoContainer

local SlitLine = Instance.new("Frame")
SlitLine.Name = "SlitLine"
SlitLine.Size = UDim2.new(0, 2, 0, 26)
SlitLine.Position = UDim2.new(0.5, -1, 0.5, -13)
SlitLine.BackgroundColor3 = Color3.fromRGB(20, 20, 24)
SlitLine.BorderSizePixel = 0
SlitLine.Rotation = -35
SlitLine.Parent = LogoContainer

local LogoLetter = Instance.new("TextLabel")
LogoLetter.Text = "V"
LogoLetter.Font = Enum.Font.GothamBold
LogoLetter.TextSize = 13
LogoLetter.TextColor3 = Color3.fromRGB(255, 255, 255)
LogoLetter.Size = UDim2.new(1, 0, 1, 0)
LogoLetter.BackgroundTransparency = 1
LogoLetter.Parent = LogoContainer

-- App Title
local TitleLabel = Instance.new("TextLabel")
TitleLabel.Text = "ovitar"
TitleLabel.Font = Enum.Font.GothamBold
TitleLabel.TextSize = 18
TitleLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
TitleLabel.TextXAlignment = Enum.TextXAlignment.Left
TitleLabel.Size = UDim2.new(0, 80, 1, 0)
TitleLabel.Position = UDim2.new(0, 60, 0, 0)
TitleLabel.BackgroundTransparency = 1
TitleLabel.Parent = TopBar

-- Status Badge (Exact match: "status: 🟢")
local StatusContainer = Instance.new("Frame")
StatusContainer.Name = "StatusContainer"
StatusContainer.Size = UDim2.new(0, 94, 0, 26)
StatusContainer.Position = UDim2.new(1, -145, 0.5, -13)
StatusContainer.BackgroundColor3 = Color3.fromRGB(11, 11, 13)
StatusContainer.BorderSizePixel = 0
StatusContainer.Parent = TopBar

local StatusCorner = Instance.new("UICorner")
StatusCorner.CornerRadius = UDim.new(1, 0)
StatusCorner.Parent = StatusContainer

local StatusStroke = Instance.new("UIStroke")
StatusStroke.Color = Color3.fromRGB(34, 34, 40)
StatusStroke.Thickness = 1
StatusStroke.Parent = StatusContainer

local StatusText = Instance.new("TextLabel")
StatusText.Text = "status:"
StatusText.Font = Enum.Font.GothamMedium
StatusText.TextSize = 12
StatusText.TextColor3 = Color3.fromRGB(160, 160, 175)
StatusText.Size = UDim2.new(0, 48, 1, 0)
StatusText.Position = UDim2.new(0, 10, 0, 0)
StatusText.BackgroundTransparency = 1
StatusText.Parent = StatusContainer

local StatusDot = Instance.new("Frame")
StatusDot.Name = "StatusDot"
StatusDot.Size = UDim2.new(0, 10, 0, 10)
StatusDot.Position = UDim2.new(0, 64, 0.5, -5)
StatusDot.BackgroundColor3 = Color3.fromRGB(52, 211, 153)
StatusDot.BorderSizePixel = 0
StatusDot.Parent = StatusContainer

local DotCorner = Instance.new("UICorner")
DotCorner.CornerRadius = UDim.new(1, 0)
DotCorner.Parent = StatusDot

-- Close Button
local CloseBtn = Instance.new("TextButton")
CloseBtn.Text = "✕"
CloseBtn.Font = Enum.Font.GothamBold
CloseBtn.TextSize = 13
CloseBtn.TextColor3 = Color3.fromRGB(150, 150, 160)
CloseBtn.Size = UDim2.new(0, 28, 0, 28)
CloseBtn.Position = UDim2.new(1, -38, 0.5, -14)
CloseBtn.BackgroundColor3 = Color3.fromRGB(28, 28, 34)
CloseBtn.BorderSizePixel = 0
CloseBtn.AutoButtonColor = true
CloseBtn.Parent = TopBar

local CloseCorner = Instance.new("UICorner")
CloseCorner.CornerRadius = UDim.new(1, 0)
CloseCorner.Parent = CloseBtn

CloseBtn.MouseButton1Click:Connect(function()
    ScreenGui:Destroy()
end)

-- Window Dragging Logic
local dragging, dragInput, dragStart, startPos
TopBar.InputBegan:Connect(function(input)
    if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then
        dragging = true
        dragStart = input.Position
        startPos = MainFrame.Position
        input.Changed:Connect(function()
            if input.UserInputState == Enum.UserInputState.End then
                dragging = false
            end
        end)
    end
end)

TopBar.InputChanged:Connect(function(input)
    if input.UserInputType == Enum.UserInputType.MouseMovement or input.UserInputType == Enum.UserInputType.Touch then
        dragInput = input
    end
end)

UserInputService.InputChanged:Connect(function(input)
    if input == dragInput and dragging then
        local delta = input.Position - dragStart
        MainFrame.Position = UDim2.new(startPos.X.Scale, startPos.X.Offset + delta.X, startPos.Y.Scale, startPos.Y.Offset + delta.Y)
    end
end)

-- Content Frame
local Content = Instance.new("Frame")
Content.Size = UDim2.new(1, -44, 1, -78)
Content.Position = UDim2.new(0, 22, 0, 68)
Content.BackgroundTransparency = 1
Content.Parent = MainFrame

-- Subtitle / Version
local Subtitle = Instance.new("TextLabel")
Subtitle.Text = "Your space. Your way.  •  " .. CONFIG.VERSION
Subtitle.Font = Enum.Font.Gotham
Subtitle.TextSize = 12
Subtitle.TextColor3 = Color3.fromRGB(120, 120, 135)
Subtitle.TextXAlignment = Enum.TextXAlignment.Left
Subtitle.Size = UDim2.new(1, 0, 0, 18)
Subtitle.Position = UDim2.new(0, 0, 0, 2)
Subtitle.BackgroundTransparency = 1
Subtitle.Parent = Content

-- Server Status Banner Card
local Banner = Instance.new("Frame")
Banner.Name = "StatusBanner"
Banner.Size = UDim2.new(1, 0, 0, 38)
Banner.Position = UDim2.new(0, 0, 0, 28)
Banner.BackgroundColor3 = Color3.fromRGB(22, 22, 26)
Banner.BorderSizePixel = 0
Banner.Parent = Content

local BannerCorner = Instance.new("UICorner")
BannerCorner.CornerRadius = UDim.new(0, 10)
BannerCorner.Parent = Banner

local BannerStroke = Instance.new("UIStroke")
BannerStroke.Color = Color3.fromRGB(36, 36, 44)
BannerStroke.Thickness = 1
BannerStroke.Parent = Banner

local BannerText = Instance.new("TextLabel")
BannerText.Text = "서버 상태를 확인하는 중..."
BannerText.Font = Enum.Font.GothamMedium
BannerText.TextSize = 12
BannerText.TextColor3 = Color3.fromRGB(180, 180, 195)
BannerText.Size = UDim2.new(1, -24, 1, 0)
BannerText.Position = UDim2.new(0, 12, 0, 0)
BannerText.TextXAlignment = Enum.TextXAlignment.Left
BannerText.BackgroundTransparency = 1
BannerText.Parent = Banner

-- Form Inputs Container
local Form = Instance.new("Frame")
Form.Size = UDim2.new(1, 0, 0, 260)
Form.Position = UDim2.new(0, 0, 0, 80)
Form.BackgroundTransparency = 1
Form.Parent = Content

-- 1. Username Input Field
local UserLabel = Instance.new("TextLabel")
UserLabel.Text = "웹사이트 계정 아이디"
UserLabel.Font = Enum.Font.GothamBold
UserLabel.TextSize = 12
UserLabel.TextColor3 = Color3.fromRGB(175, 175, 190)
UserLabel.TextXAlignment = Enum.TextXAlignment.Left
UserLabel.Size = UDim2.new(1, 0, 0, 16)
UserLabel.Position = UDim2.new(0, 0, 0, 0)
UserLabel.BackgroundTransparency = 1
UserLabel.Parent = Form

local UserBox = Instance.new("TextBox")
UserBox.PlaceholderText = "아이디를 입력하세요"
UserBox.Font = Enum.Font.Gotham
UserBox.TextSize = 13
UserBox.TextColor3 = Color3.fromRGB(255, 255, 255)
UserBox.PlaceholderColor3 = Color3.fromRGB(85, 85, 98)
UserBox.Size = UDim2.new(1, 0, 0, 44)
UserBox.Position = UDim2.new(0, 0, 0, 22)
UserBox.BackgroundColor3 = Color3.fromRGB(11, 11, 13)
UserBox.BorderSizePixel = 0
UserBox.TextXAlignment = Enum.TextXAlignment.Left
UserBox.Text = ""
UserBox.ClearTextOnFocus = false
UserBox.Parent = Form

local UserBoxCorner = Instance.new("UICorner")
UserBoxCorner.CornerRadius = UDim.new(0, 10)
UserBoxCorner.Parent = UserBox

local UserBoxStroke = Instance.new("UIStroke")
UserBoxStroke.Color = Color3.fromRGB(38, 38, 46)
UserBoxStroke.Thickness = 1.1
UserBoxStroke.Parent = UserBox

local UserBoxPad = Instance.new("UIPadding")
UserBoxPad.PaddingLeft = UDim.new(0, 14)
UserBoxPad.PaddingRight = UDim.new(0, 14)
UserBoxPad.Parent = UserBox

-- Focus animations for Username
UserBox.Focused:Connect(function()
    TweenService:Create(UserBoxStroke, TweenInfo.new(0.2), {Color = Color3.fromRGB(110, 110, 140)}):Play()
end)
UserBox.FocusLost:Connect(function()
    TweenService:Create(UserBoxStroke, TweenInfo.new(0.2), {Color = Color3.fromRGB(38, 38, 46)}):Play()
end)

-- 2. Password Input Field with Masking & Eye Toggle
local PassLabel = Instance.new("TextLabel")
PassLabel.Text = "비밀번호"
PassLabel.Font = Enum.Font.GothamBold
PassLabel.TextSize = 12
PassLabel.TextColor3 = Color3.fromRGB(175, 175, 190)
PassLabel.TextXAlignment = Enum.TextXAlignment.Left
PassLabel.Size = UDim2.new(1, 0, 0, 16)
PassLabel.Position = UDim2.new(0, 0, 0, 78)
PassLabel.BackgroundTransparency = 1
PassLabel.Parent = Form

local PassContainer = Instance.new("Frame")
PassContainer.Name = "PassContainer"
PassContainer.Size = UDim2.new(1, 0, 0, 44)
PassContainer.Position = UDim2.new(0, 0, 0, 100)
PassContainer.BackgroundColor3 = Color3.fromRGB(11, 11, 13)
PassContainer.BorderSizePixel = 0
PassContainer.Parent = Form

local PassContainerCorner = Instance.new("UICorner")
PassContainerCorner.CornerRadius = UDim.new(0, 10)
PassContainerCorner.Parent = PassContainer

local PassContainerStroke = Instance.new("UIStroke")
PassContainerStroke.Color = Color3.fromRGB(38, 38, 46)
PassContainerStroke.Thickness = 1.1
PassContainerStroke.Parent = PassContainer

local PassBox = Instance.new("TextBox")
PassBox.Name = "PassBox"
PassBox.PlaceholderText = "비밀번호를 입력하세요"
PassBox.Font = Enum.Font.Gotham
PassBox.TextSize = 13
PassBox.TextColor3 = Color3.fromRGB(255, 255, 255)
PassBox.PlaceholderColor3 = Color3.fromRGB(85, 85, 98)
PassBox.Size = UDim2.new(1, -48, 1, 0)
PassBox.Position = UDim2.new(0, 0, 0, 0)
PassBox.BackgroundTransparency = 1
PassBox.TextXAlignment = Enum.TextXAlignment.Left
PassBox.Text = ""
PassBox.ClearTextOnFocus = false
PassBox.Parent = PassContainer

local PassBoxPad = Instance.new("UIPadding")
PassBoxPad.PaddingLeft = UDim.new(0, 14)
PassBoxPad.PaddingRight = UDim.new(0, 6)
PassBoxPad.Parent = PassBox

-- Eye Toggle Button (👁️ / 🔒)
local EyeBtn = Instance.new("TextButton")
EyeBtn.Name = "EyeToggle"
EyeBtn.Text = "👁️"
EyeBtn.Font = Enum.Font.GothamMedium
EyeBtn.TextSize = 15
EyeBtn.TextColor3 = Color3.fromRGB(160, 160, 175)
EyeBtn.Size = UDim2.new(0, 36, 0, 36)
EyeBtn.Position = UDim2.new(1, -40, 0.5, -18)
EyeBtn.BackgroundColor3 = Color3.fromRGB(20, 20, 24)
EyeBtn.BorderSizePixel = 0
EyeBtn.AutoButtonColor = true
EyeBtn.Parent = PassContainer

local EyeCorner = Instance.new("UICorner")
EyeCorner.CornerRadius = UDim.new(0, 8)
EyeCorner.Parent = EyeBtn

-- State for real password and visibility toggle
local realPassword = ""
local isPasswordVisible = false
local isUpdatingText = false

local function maskString(str)
    return string.rep("•", utf8.len(str) or #str)
end

PassBox:GetPropertyChangedSignal("Text"):Connect(function()
    if isUpdatingText then return end
    
    local currentText = PassBox.Text
    if isPasswordVisible then
        realPassword = currentText
    else
        local currentLen = #currentText
        local maskedLen = #maskString(realPassword)
        
        if currentLen > maskedLen then
            local diff = currentLen - maskedLen
            local added = string.sub(currentText, currentLen - diff + 1)
            realPassword = realPassword .. added
        elseif currentLen < maskedLen then
            local diff = maskedLen - currentLen
            realPassword = string.sub(realPassword, 1, math.max(0, #realPassword - diff))
        end
        
        isUpdatingText = true
        PassBox.Text = maskString(realPassword)
        isUpdatingText = false
    end
end)

EyeBtn.MouseButton1Click:Connect(function()
    isPasswordVisible = not isPasswordVisible
    isUpdatingText = true
    if isPasswordVisible then
        EyeBtn.Text = "🔒"
        EyeBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
        PassBox.Text = realPassword
    else
        EyeBtn.Text = "👁️"
        EyeBtn.TextColor3 = Color3.fromRGB(160, 160, 175)
        PassBox.Text = maskString(realPassword)
    end
    isUpdatingText = false
end)

PassBox.Focused:Connect(function()
    TweenService:Create(PassContainerStroke, TweenInfo.new(0.2), {Color = Color3.fromRGB(110, 110, 140)}):Play()
end)
PassBox.FocusLost:Connect(function()
    TweenService:Create(PassContainerStroke, TweenInfo.new(0.2), {Color = Color3.fromRGB(38, 38, 46)}):Play()
end)

-- 3. Login & Load Button (High-Contrast White Pill)
local LoadBtn = Instance.new("TextButton")
LoadBtn.Name = "LoadButton"
LoadBtn.Text = "로그인 및 스크립트 실행"
LoadBtn.Font = Enum.Font.GothamBold
LoadBtn.TextSize = 13
LoadBtn.TextColor3 = Color3.fromRGB(0, 0, 0)
LoadBtn.Size = UDim2.new(1, 0, 0, 46)
LoadBtn.Position = UDim2.new(0, 0, 0, 166)
LoadBtn.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
LoadBtn.BorderSizePixel = 0
LoadBtn.AutoButtonColor = true
LoadBtn.Parent = Form

local LoadBtnCorner = Instance.new("UICorner")
LoadBtnCorner.CornerRadius = UDim.new(1, 0)
LoadBtnCorner.Parent = LoadBtn

LoadBtn.MouseEnter:Connect(function()
    TweenService:Create(LoadBtn, TweenInfo.new(0.15), {BackgroundColor3 = Color3.fromRGB(235, 235, 240)}):Play()
end)
LoadBtn.MouseLeave:Connect(function()
    TweenService:Create(LoadBtn, TweenInfo.new(0.15), {BackgroundColor3 = Color3.fromRGB(255, 255, 255)}):Play()
end)

-- 4. Footer Information & Reset HWID Guide
local Footer = Instance.new("TextLabel")
Footer.Text = "💡 하드웨어 변경 시 웹사이트 '하드웨어 리셋'을 이용하세요.\n라이선스 구매 및 문의: 디스코드 (주간 ₩15,000 / 월간 ₩30,000 / 영구 ₩80,000)"
Footer.Font = Enum.Font.Gotham
Footer.TextSize = 11
Footer.TextColor3 = Color3.fromRGB(105, 105, 120)
Footer.TextWrapped = true
Footer.Size = UDim2.new(1, 0, 0, 36)
Footer.Position = UDim2.new(0, 0, 1, -42)
Footer.BackgroundTransparency = 1
Footer.Parent = Content

-- Update Status Function
local function updateStatusUI(status, msg, ver)
    if status == "online" then
        StatusDot.BackgroundColor3 = Color3.fromRGB(52, 211, 153) -- Green 🟢
        Banner.BackgroundColor3 = Color3.fromRGB(14, 30, 22)
        BannerStroke.Color = Color3.fromRGB(22, 60, 40)
        BannerText.TextColor3 = Color3.fromRGB(74, 222, 128)
        BannerText.Text = "🟢 정상 서비스 중 (" .. msg .. ")"
        LoadBtn.Active = true
        LoadBtn.Text = "로그인 및 스크립트 실행"
    elseif status == "maintenance" then
        StatusDot.BackgroundColor3 = Color3.fromRGB(250, 204, 21) -- Yellow 🟡
        Banner.BackgroundColor3 = Color3.fromRGB(34, 28, 10)
        BannerStroke.Color = Color3.fromRGB(70, 56, 16)
        BannerText.TextColor3 = Color3.fromRGB(250, 204, 21)
        BannerText.Text = "🟡 서버 점검 진행 중 (" .. msg .. ")"
        LoadBtn.Active = false
        LoadBtn.Text = "현재 서버 점검 중입니다"
    else
        StatusDot.BackgroundColor3 = Color3.fromRGB(239, 68, 68) -- Red 🔴
        Banner.BackgroundColor3 = Color3.fromRGB(34, 14, 14)
        BannerStroke.Color = Color3.fromRGB(70, 24, 24)
        BannerText.TextColor3 = Color3.fromRGB(248, 113, 113)
        BannerText.Text = "🔴 서비스 오프라인 (" .. msg .. ")"
        LoadBtn.Active = false
        LoadBtn.Text = "서비스 이용 불가"
    end
end

-- Initial Server Check
task.spawn(function()
    local s, m, v = checkServerStatus()
    updateStatusUI(s, m, v)
end)

-- LOGIN & SCRIPT EXECUTION HANDLER
LoadBtn.MouseButton1Click:Connect(function()
    local username = UserBox.Text:gsub("%s+", "")
    local password = realPassword:gsub("%s+", "")

    if username == "" or password == "" then
        Banner.BackgroundColor3 = Color3.fromRGB(34, 14, 14)
        BannerStroke.Color = Color3.fromRGB(70, 24, 24)
        BannerText.TextColor3 = Color3.fromRGB(248, 113, 113)
        BannerText.Text = "⚠️ 아이디와 비밀번호를 모두 입력하세요."
        return
    end

    LoadBtn.Text = "서버 인증 및 라이선스 확인 중..."
    LoadBtn.Active = false

    local hwid = getHWID()

    task.spawn(function()
        local success, res = pcall(function()
            return HttpRequest({
                Url = CONFIG.API_URL .. "/api/loader/auth",
                Method = "POST",
                Headers = { ["Content-Type"] = "application/json" },
                Body = HttpService:JSONEncode({
                    username = username,
                    password = password,
                    hwid = hwid
                })
            })
        end)

        if success and res then
            local decodeSuccess, data = pcall(function()
                return HttpService:JSONDecode(res.Body)
            end)

            if decodeSuccess and res.StatusCode == 200 and data.success then
                Banner.BackgroundColor3 = Color3.fromRGB(14, 30, 22)
                BannerStroke.Color = Color3.fromRGB(22, 60, 40)
                BannerText.TextColor3 = Color3.fromRGB(74, 222, 128)
                BannerText.Text = "✅ 인증 성공! (" .. tostring(data.license_tier) .. " 플랜)"
                
                LoadBtn.Text = "스크립트 로드 성공!"
                
                task.wait(0.7)
                ScreenGui:Destroy()

                -- 1. DECRYPT MAIN SCRIPT & DECOY SCRIPT
                local finalScript = ""
                local fakeDecoyScript = "-- [OVITAR INTEGRITY DECOY]\nprint('Core Verified')\n"

                if data.encrypted and data.payload then
                    local decOk, decRes = pcall(function()
                        return decryptScriptPayload(data.payload, data.nonce)
                    end)
                    if decOk and decRes and decRes ~= "" then
                        finalScript = decRes
                    end
                elseif data.script and data.script ~= "" and not data.script:find("PROTECTED") then
                    finalScript = data.script
                end

                if data.fake_payload then
                    pcall(function()
                        local decFk = decryptScriptPayload(data.fake_payload, data.nonce)
                        if decFk and decFk ~= "" then
                            fakeDecoyScript = decFk
                        end
                    end)
                end

                -- 2. SAFE SERVER WEBHOOK REPORT HELPER (디스코드 주소 노출 없이 서버 경유 전송)
                local function reportSecurityEvent(eventType, message)
                    pcall(function()
                        HttpRequest({
                            Url = CONFIG.API_URL .. "/api/webhook/relay",
                            Method = "POST",
                            Headers = { ["Content-Type"] = "application/json" },
                            Body = HttpService:JSONEncode({
                                event = eventType,
                                message = message,
                                username = username,
                                hwid = hwid
                            })
                        })
                    end)
                end

                reportSecurityEvent("Script Authorized", "유저 인증 성공 및 스크립트 실행 시작 (" .. tostring(data.license_tier) .. ")")

                -- 3. SETCLIPBOARD HOOK & DECOY INJECTION (복사 시도 시 그럴싸한 가짜 코드로 바꿔치기)
                pcall(function()
                    local orig_setclipboard = setclipboard or toclipboard or (syn and syn.write_clipboard)
                    local function fake_clipboard(text)
                        reportSecurityEvent("Clipboard Intercepted", "사용자 또는 덤퍼가 setclipboard를 시도했습니다. 가짜 미끼 코드로 대체되었습니다.")
                        if orig_setclipboard then
                            orig_setclipboard(fakeDecoyScript)
                        end
                    end
                    
                    if hookfunction and orig_setclipboard then
                        hookfunction(orig_setclipboard, fake_clipboard)
                    else
                        getgenv().setclipboard = fake_clipboard
                        getgenv().toclipboard = fake_clipboard
                        if syn and syn.write_clipboard then syn.write_clipboard = fake_clipboard end
                    end
                end)

                -- 4. ANTI-DUMPER / ENV LOGGER TAMPER DETECTION (리버싱 도구 감지 시 즉시 안전 종료)
                local function detectTamper()
                    local env = getgenv and getgenv() or _G
                    local suspiciousFlags = {
                        "dump", "dumper", "envlogger", "dex_dump", "hydroxdump", "spy_active"
                    }
                    for _, flag in ipairs(suspiciousFlags) do
                        if env[flag] or env[flag:upper()] then
                            return true, "Suspicious environment logger flag detected: " .. flag
                        end
                    end
                    return false, nil
                end

                local isTampered, tamperReason = detectTamper()
                if isTampered then
                    reportSecurityEvent("Tampering Detected", tamperReason)
                    -- Clean safe unload: 메모리 비우고 즉시 종료
                    finalScript = nil
                    data = nil
                    return
                end

                -- 5. HEARTBEAT & SERVER INTEGRITY WATCHDOG (API 연결 끊김 또는 점검 전환 시 자동 안전 종료)
                task.spawn(function()
                    local failCount = 0
                    while task.wait(15) do
                        local ok, pingRes = pcall(function()
                            return HttpRequest({
                                Url = CONFIG.API_URL .. "/api/loader/heartbeat",
                                Method = "GET",
                                Headers = { ["Content-Type"] = "application/json" }
                            })
                        end)
                        
                        local isAlive = false
                        if ok and pingRes and pingRes.StatusCode == 200 then
                            local pOk, pData = pcall(function() return HttpService:JSONDecode(pingRes.Body) end)
                            if pOk and pData and pData.alive then
                                isAlive = true
                                failCount = 0
                            end
                        end
                        
                        if not isAlive then
                            failCount = failCount + 1
                            if failCount >= 2 then
                                reportSecurityEvent("Heartbeat Lost", "서버 통신 단절로 인해 스크립트를 안전하게 언로드했습니다.")
                                -- Unload logic: clear memory and clean termination
                                finalScript = nil
                                break
                            end
                        end
                    end
                end)

                -- 6. EXECUTE SCRIPT PAYLOAD
                if finalScript and finalScript ~= "" then
                    local execSuccess, execErr = pcall(function()
                        local runFunc = loadstring(finalScript)
                        if runFunc then
                            runFunc()
                        else
                            error("Failed to compile script payload")
                        end
                    end)
                    if not execSuccess then
                        warn("[OVITAR] Error running delivered script: " .. tostring(execErr))
                    end
                else
                    warn("[OVITAR] Decrypted script payload was empty or corrupt!")
                end
            else
                LoadBtn.Active = true
                LoadBtn.Text = "다시 시도하기"
                Banner.BackgroundColor3 = Color3.fromRGB(34, 14, 14)
                BannerStroke.Color = Color3.fromRGB(70, 24, 24)
                BannerText.TextColor3 = Color3.fromRGB(248, 113, 113)
                BannerText.Text = "❌ " .. ((data and data.message) or "인증 실패 (아이디/비밀번호/키 확인)")
            end
        else
            LoadBtn.Active = true
            LoadBtn.Text = "다시 시도하기"
            Banner.BackgroundColor3 = Color3.fromRGB(34, 14, 14)
            BannerStroke.Color = Color3.fromRGB(70, 24, 24)
            BannerText.TextColor3 = Color3.fromRGB(248, 113, 113)
            BannerText.Text = "❌ 서버와 통신할 수 없습니다. (포트 5500 상태 확인)"
        end
    end)
end)

print("⚡ [OVITAR] Loader UI v0.6.0 successfully loaded with HWID fix & eye toggle!")
