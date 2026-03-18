import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import unquote
from Utils import version_tuple


def write_json(handler, data, status=200):
    body = json.dumps(data).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def build_room_info(ctx):
    games = {ctx.games[x] for x in range(1, len(ctx.games) + 1)}
    games.add("Archipelago")
    from MultiServer import get_permissions
    return {
        "password": bool(ctx.password),
        "games": sorted(games),
        "tags": sorted(ctx.tags),
        "version": list(version_tuple),
        "generator_version": list(ctx.generator_version),
        "permissions": get_permissions(ctx),
        "hint_cost": ctx.hint_cost,
        "location_check_points": ctx.location_check_points,
        "datapackage_checksums": {
            game: game_data["checksum"]
            for game, game_data in ctx.gamespackage.items()
            if game in games and "checksum" in game_data
        },
        "seed_name": ctx.seed_name,
        "time": time.time(),
    }


def build_players(ctx):
    result = []
    for player in ctx.get_players_package():
        result.append({
            "team": player.team,
            "slot": player.slot,
            "alias": player.alias,
            "name": player.name,
        })
    return result


def build_player(ctx, slot):
    info = ctx.slot_info[slot]
    return {
        "slot": slot,
        "name": info.name,
        "game": info.game,
        "type": int(info.type),
        "group_members": info.group_members,
    }


def build_slot_data(ctx, slot):
    return ctx.slot_data[slot]


def build_locations(ctx, slot):
    result = {}
    for location_id, (item_id, receiving_slot, flags) in ctx.locations[slot].items():
        result[str(location_id)] = {
            "item": item_id,
            "player": receiving_slot,
            "flags": flags,
        }
    return result


def build_checks(ctx, team, slot):
    return {
        "team": team,
        "slot": slot,
        "locations": list(ctx.location_checks.get((team, slot), set())),
    }


def build_received(ctx, team, slot):
    items = ctx.received_items.get((team, slot, True), [])
    return [
        {
            "item": item.item,
            "location": item.location,
            "player": item.player,
            "flags": item.flags,
        }
        for item in items
    ]


def build_datapackage(ctx, game):
    return {
        "games": {
            game: ctx.gamespackage[game]
        }
    }


class ApiHandler(BaseHTTPRequestHandler):
    ctx = None

    def do_GET(self):
        parts = self.path.strip("/").split("/")
    
        # GET /room_info
        # Returns room metadata (matches Archipelago RoomInfo packet)
        if self.path == "/room_info":
            write_json(self, build_room_info(ApiHandler.ctx))
            return
    
        # GET /players
        # Returns list of all players (team, slot, alias, name)
        if self.path == "/players":
            write_json(self, build_players(ApiHandler.ctx))
            return
    
        # GET /player/<slot>
        # Returns slot metadata for a specific player/world
        if len(parts) == 2 and parts[0] == "player":
            write_json(self, build_player(ApiHandler.ctx, int(parts[1])))
            return
    
        # GET /slot_data/<slot>
        # Returns generation settings for a slot (Connected.slot_data)
        if len(parts) == 2 and parts[0] == "slot_data":
            write_json(self, build_slot_data(ApiHandler.ctx, int(parts[1])))
            return
    
        # GET /locations/<slot>
        # Returns full world layout for a slot:
        # location_id -> (item_id, receiving_slot, flags)
        if len(parts) == 2 and parts[0] == "locations":
            write_json(self, build_locations(ApiHandler.ctx, int(parts[1])))
            return
    
        # GET /checks/<team>/<slot>
        # Returns list of checked location IDs for that player
        if len(parts) == 3 and parts[0] == "checks":
            write_json(self, build_checks(ApiHandler.ctx, int(parts[1]), int(parts[2])))
            return
    
        # GET /received/<team>/<slot>
        # Returns items received by that player from any world
        if len(parts) == 3 and parts[0] == "received":
            write_json(self, build_received(ApiHandler.ctx, int(parts[1]), int(parts[2])))
            return
    
        # GET /datapackage/<game>
        # Returns data package for a game (item/location ID mappings)
        if len(parts) == 2 and parts[0] == "datapackage":
            write_json(self, build_datapackage(ApiHandler.ctx, unquote(parts[1])))
            return
    
        write_json(self, {"error": "not found"}, 404)
    def log_message(self, format, *args):
        pass


def start_api(ctx, host="127.0.0.1", port=38282):
    ApiHandler.ctx = ctx
    server = ThreadingHTTPServer((host, port), ApiHandler)
    Thread(target=server.serve_forever, daemon=True).start()
    return server