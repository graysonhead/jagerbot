from esipy import EsiClient
from esipy import EsiApp
from math import sqrt
import datetime

jumps = {"data": [], "expiry": None}

kills = {"data": [], "expiry": None}

client = EsiClient(
    retry_requests=True,  # set to retry on http 5xx error (default False)
    headers={'User-Agent': 'Jagerbot'},
    raw_body_only=False,  # default False, set to True to never parse response and only return raw JSON string content.
)
esi_app = EsiApp()
app = esi_app.get_latest_swagger


def get_jumps():
    if jumps['expiry'] is None or jumps['expiry'] < datetime.datetime.utcnow():
        get_system_jumps = app.op['get_universe_system_jumps']()
        jump_resp = client.request(get_system_jumps)
        jumps.update({"data": jump_resp.data})
        jumps.update({"expiry": datetime.datetime.utcnow() + datetime.timedelta(seconds=90)})
        return jumps['data']
    else:
        return jumps['data']


def get_kills():
    if kills['expiry'] is None or kills['expiry'] < datetime.datetime.utcnow():
        get_system_kills = app.op['get_universe_system_kills']()
        kill_resp = client.request(get_system_kills)
        kills.update({"data": kill_resp.data})
        kills.update({"expiry": datetime.datetime.utcnow() + datetime.timedelta(seconds=90)})
        return kills['data']
    else:
        return kills['data']


def get_systems_from_constellation(constellation_id):
    system_ids = []
    get_constellation = app.op['get_universe_constellations_constellation_id'](
        constellation_id=constellation_id
    )
    resp = client.request(get_constellation)
    for system in resp.data['systems']:
        system_ids.append(system)
    return system_ids


def get_systems_from_region(region_id):
    get_regions = app.op['get_universe_regions_region_id'](
        region_id=region_id
    )
    system_ids = []
    system_objects = []
    resp = client.request(get_regions)
    constellations = resp.data['constellations']
    for constellation in constellations:
        const = get_systems_from_constellation(constellation)
        for system in const:
            system_ids.append(system)
    for system in system_ids:
        system_objects.append(get_system_info(system))
    return system_objects


def get_system_info(system_id):
    get_system = app.op['get_universe_systems_system_id'](
        system_id=system_id
    )
    resp = client.request(get_system)
    return resp.data


def get_system_by_name(name):
    get_system = app.op['get_search'](
        search=name,
        categories=['solar_system']
    )
    resp = client.request(get_system)
    system_id = resp.data['solar_system'][0]
    return get_system_info(system_id)


class Position:

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return f"<Position(x={self.x}, y={self.y}, z={self.z})>"

    def calculate_distance(self, other):
        a = self
        b = other
        return (((sqrt(((a.x - b.x) * (a.x - b.x)) + ((a.y - b.y) * (a.y - b.y)) + (
                    (a.z - b.z) * (a.z - b.z)))) / 149597870691) / 63239.6717)


class SystemStats:

    def __init__(self, npc_kills: int, pod_kills: int, ship_kills: int, ship_jumps: int):
        self.npc_kills = npc_kills
        self.pod_kills = pod_kills
        self.ship_kills = ship_kills
        self.ship_jumps = ship_jumps

    def __repr__(self):
        return f"<SystemStats(npc_kills={self.npc_kills}, pod_kills={self.pod_kills}, ship_kills={self.ship_kills}, ship_jumps={self.ship_jumps})>"

    @classmethod
    def get_by_system_id(cls, system_id):
        jump_dict = get_jumps()
        kill_dict = get_kills()
        try:
            jump_dict = next(filter(lambda x: x.system_id == system_id, jump_dict))
            ship_jumps = jump_dict['ship_jumps']
        except StopIteration:
            ship_jumps = 0
        try:
            kill_dict = next(filter(lambda x: x.system_id == system_id, kill_dict))
            npc_kills = kill_dict['npc_kills']
            ship_kills = kill_dict['ship_kills']
            pod_kills = kill_dict['pod_kills']
        except StopIteration:
            npc_kills = 0
            ship_kills = 0
            pod_kills = 0
        return SystemStats(npc_kills, pod_kills, ship_kills, ship_jumps)


class SolarSystem:

    def __init__(self,
                 system_id: int,
                 constellation_id: int,
                 name: str,
                 position: Position,
                 security_status: int,
                 stats: SystemStats):
        self.system_id = system_id
        self.constellation_id = constellation_id
        self.name = name
        self.position = position
        self.security_status = security_status
        self.stats = stats

    def distance_to(self, other):
        return self.position.calculate_distance(other.position)

    def update_stats(self):
        stats = SystemStats.get_by_system_id(self.system_id)

    @classmethod
    def get_by_name(cls, name):
        get_system = app.op['get_search'](
            search=name,
            categories=['solar_system']
        )
        resp = client.request(get_system)
        system_id = resp.data['solar_system'][0]
        return cls.get_by_id(system_id)

    @classmethod
    def get_by_id(cls, system_id):
        get_system = app.op['get_universe_systems_system_id'](
            system_id=system_id
        )
        resp = client.request(get_system)
        stats = SystemStats.get_by_system_id(system_id)
        return SolarSystem(resp.data['system_id'],
                           resp.data['constellation_id'],
                           resp.data['name'],
                           Position(resp.data['position']['x'],
                                    resp.data['position']['y'],
                                    resp.data['position']['z']),
                           resp.data['security_status'],
                           stats
                           )

    def __repr__(self):
        return f"<SolarSystem(name=\"{self.name}\", id=\"{self.system_id}\")>"


class KillFilter:

    def __init__(self, npc_kills=None, pod_kills=None, jumps=None, ship_kills=None):
        self.npc_kills = npc_kills
        self.pod_kills = pod_kills
        self.ship_jumps = jumps
        self.ship_kills = ship_kills


class RangeFilter:

    def __init__(self, system: SolarSystem, range: int):
        self.system = system
        self.range = range


class Constellation:

    def __init__(self, name: str, constellation_id: int, position: Position, systems: list):
        self.name = name
        self.constellation_id = constellation_id,
        self.position = position
        self.systems = systems

    def __repr__(self):
        return f"<Constellation(name=\"{self.name}\", constellation_id={self.constellation_id}, position={self.position})>"

    def search_systems(self,  kill_filter: KillFilter = KillFilter(), range_filter: RangeFilter = None):
        if range_filter:
            systems = self.get_systems_within_range(range_filter.system, range_filter.range)
        else:
            systems = self.systems

        if kill_filter:
            try:
                if kill_filter.ship_jumps:
                    systems = list(filter(lambda x: x.stats.ship_jumps >= kill_filter.ship_jumps, systems))
                if kill_filter.ship_kills:
                    systems = list(filter(lambda x: x.stats.ship_kills >= kill_filter.ship_kills, systems))
                if kill_filter.pod_kills:
                    systems = list(filter(lambda x: x.stats.pod_kills >= kill_filter.pod_kills, systems))
                if kill_filter.npc_kills:
                    systems = list(filter(lambda x: x.stats.npc_kills >= kill_filter.npc_kills, systems))
            except StopIteration:
                return []
        return systems

    def get_systems_within_range(self, system: SolarSystem, range: int):
        systems_in_range = []
        systems = self.systems
        for other_system in systems:
            if system.distance_to(other_system) <= range:
                systems_in_range.append(other_system)
        return systems_in_range

    def update_stats(self):
        for system in self.systems:
            system.update_stats()

    @classmethod
    def get_by_name(cls, name: str):
        get_constellation = app.op['get_search'](
            search=name,
            categories=['constellation']
        )
        resp = client.request(get_constellation)
        constellation_id = resp.data['constellation'][0]
        return cls.get_by_id(constellation_id)

    @classmethod
    def get_by_id(cls, constellation_id: int):
        get_constellation = app.op['get_universe_constellations_constellation_id'](
            constellation_id=constellation_id
        )
        resp = client.request(get_constellation)
        resp = resp.data
        pos = Position(resp['position']['x'], resp['position']['y'], resp['position']['z'])
        name = resp['name']
        constellation_id = resp['constellation_id']
        systems = []
        for system_id in resp['systems']:
            systems.append(SolarSystem.get_by_id(system_id))
        return Constellation(name, constellation_id, pos, systems)


class Region:

    def __init__(self, name: str, descripton: str, region_id: int, constellations: list):
        self.name = name,
        self.description = descripton,
        self.region_id = region_id
        self.constellations = constellations

    def search_systems(self, kill_filter: KillFilter = KillFilter(), range_filter: RangeFilter = None):
        systems = []
        for constellation in self.constellations:
            for system in constellation.search_systems(kill_filter, range_filter):
                systems.append(system)
        return systems

    def get_systems(self):
        systems = []
        for constellation in self.constellations:
            for system in constellation.systems:
                systems.append(system)
        return systems

    def get_systems_within_range(self, system: SolarSystem, range: int):
        systems_in_range = []
        systems = self.get_systems()
        for other_system in systems:
            if system.distance_to(other_system) <= range:
                systems_in_range.append(other_system)
        return systems_in_range

    def update_stats(self):
        for constellation in self.constellations:
            constellation.update_stats()

    @classmethod
    def get_by_name(cls, region_name):
        get_region = app.op['get_search'](
            search=region_name,
            categories=['region']
        )
        resp = client.request(get_region)
        return cls.get_by_id(resp.data['region'][0])

    @classmethod
    def get_by_id(cls, region_id):
        get_region = app.op['get_universe_regions_region_id'](
            region_id=region_id
        )
        resp = client.request(get_region)
        name = resp.data['name']
        description = resp.data['description']
        constellations = []
        for constellation_id in resp.data['constellations']:
            constellations.append(Constellation.get_by_id(constellation_id))
        return Region(name, description, region_id, constellations)


