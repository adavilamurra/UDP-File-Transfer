-- Echo protocol example
-- author: Team Echo

local echo_proto = Proto("echoProto","Echo Protocol")

-- create a function to dissect it
function echo_proto.dissector(buffer,pinfo,tree)
    pinfo.cols.protocol = "ECHO"
    local subtree = tree:add(echo_proto,buffer(),"Echo Protocol Data")

	-- Message is at least three bytes long
	if buffer:len() < 3 then
		subtree:add_expert_info(PI_MALFORMED, PI_ERROR, "Invalid Message")
		return end
	
	-- All messages have a sequence number and type
    i = 0
    local type = buffer(i,1):uint()
    if type == 1 then
        subtree.add(buffer(i,1), "Put:" .. type)
    elseif type == 2 then
        subtree.add(buffer(i, 1), "Gett:" .. type)
    else
        subtree.add("Invalid Type.")
    end
    i = i + 2
    local fileID= buffer(i, 1):uint()
    subtree:add(buffer(i,1),"Identifier: " .. fileID)
    i = i + 2
    local prevI = i
    local character = buffer(i, 1):string()
    while character ~= ":" do
        i = i + 1
        character = buffer(i, 1):string()
    end
    local packetNum = buffer(prevI,i-1):uint()
    subtree:add(buffer(prevI, i-1),"Packet Number: " .. packetNum)
    i = i + 1
    prevI = i
    character = buffer(i, 1):string()
    while character ~= "*" do
        i = i + 1
        character = buffer(i, 1):string()
    end
    local fileSize = buffer(prevI,i-1):uint()
    subtree:add(buffer(prevI, i-1),"File Size: " .. fileSize)
    local msg = buffer(i):string() 
    subtree:add(buffer(i),"Message: " .. msg)
end

-- load the udp.port table
udp_table = DissectorTable.get("udp.port")
-- register protocol to handle udp ports
udp_table:add(5000,echo_proto)
udp_table:add(5001,echo_proto) 
udp_table:add(5002,echo_proto)
 
-- original source code and getting started
-- https://shloemi.blogspot.com/2011/05/guide-creating-your-own-fast-wireshark.html

-- helpful links
-- https://delog.wordpress.com/2010/09/27/create-a-wireshark-dissector-in-lua/
-- https://wiki.wireshark.org/LuaAPI/Tvb
-- http://lua-users.org/wiki/LuaTypesTutorial
-- https://wiki.wireshark.org/Lua/Examples
-- https://wiki.wireshark.org/LuaAPI/Proto
-- https://www.wireshark.org/docs/wsdg_html_chunked/wslua_dissector_example.html
-- https://www.wireshark.org/lists/wireshark-users/201206/msg00010.html
-- https://wiki.wireshark.org/LuaAPI/TreeItem
-- https://www.wireshark.org/docs/man-pages/tshark.html


