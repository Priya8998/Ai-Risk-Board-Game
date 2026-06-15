import random

class SimpleAI:
    """A minimal AI that uses the Environment API:
    - Deploy: randomly distributes available troops to owned territories
    - Attack: repeatedly attack random enemy-neighboring territories while possible
    - Move after attack: move minimum required troops
    - Fortify: move one troop from a non-front territory to a front if possible
    """
    def __init__(self, env, player_id):
        self.env = env
        self.player_id = player_id

    def take_turn(self):
        # Ensure it's our turn
        if self.env.curr_player.id != self.player_id:
            return

        # DEPLOY
        while self.env.curr_player.curr_troops_num > 0:
            owned = [i for i, r in enumerate(self.env.curr_gamestate) if r[0] == self.player_id]
            if not owned:
                break
            tid = random.choice(owned)
            # deploy 1 troop at a time to avoid overshooting checks
            try:
                self.env.deploy(tid, 1)
            except Exception:
                break

        # CHANGE TO ATTACK
        try:
            self.env.change_phase()
        except Exception:
            pass

        # ATTACK: keep attempting attacks from any owned territory with >1 troops
        attacked = True
        attempts = 0
        while attacked and attempts < 200:
            attempts += 1
            attacked = False
            for t_from, state in enumerate(self.env.curr_gamestate):
                if state[0] != self.player_id or state[1] <= 1:
                    continue
                # check neighbours for enemies
                neighbours = [t for n, t in self.env.map['territories'].items() if t['id'] == t_from]
                # territories mapping in this codebase stores neighbours by name, so find ids
                # We'll fallback to scanning all territories to find neighbors' ids by name
                neigh_ids = []
                try:
                    t_obj = [t for n, t in self.env.map['territories'].items() if t['id'] == t_from][0]
                    for neigh_name in t_obj['neighbours']:
                        nid = [t['id'] for n, t in self.env.map['territories'].items() if t['name'] == neigh_name]
                        if nid:
                            neigh_ids.append(nid[0])
                except Exception:
                    continue

                enemy_targets = [nid for nid in neigh_ids if self.env.curr_gamestate[nid][0] != self.player_id]
                if not enemy_targets:
                    continue

                # attack a random enemy neighbor
                target = random.choice(enemy_targets)
                try:
                    min_troops = self.env.attack(t_from, target)
                except Exception:
                    continue

                attacked = True
                # if won, move the minimum troops
                if min_troops and min_troops > 0:
                    try:
                        self.env.move_after_attack(t_from, target, min_troops, min_troops)
                    except Exception:
                        pass

                # break to re-evaluate game state
                break

        # CHANGE TO FORTIFY
        try:
            self.env.change_phase()
        except Exception:
            pass

        # FORTIFY: move one troop from an interior territory to a front if possible
        try:
            owned = [i for i, r in enumerate(self.env.curr_gamestate) if r[0] == self.player_id and r[1] > 1]
            for tid in owned:
                # find a neighbour owned by same player that is a front (has enemy neighbor)
                try:
                    t_obj = [t for n, t in self.env.map['territories'].items() if t['id'] == tid][0]
                except Exception:
                    continue
                neigh_ids = []
                for neigh_name in t_obj['neighbours']:
                    nid = [t['id'] for n, t in self.env.map['territories'].items() if t['name'] == neigh_name]
                    if nid:
                        neigh_ids.append(nid[0])
                # find a neighbour that is also owned and is front
                for nid in neigh_ids:
                    if self.env.curr_gamestate[nid][0] == self.player_id:
                        # check if nid has enemy neighbors
                        nde = False
                        try:
                            n_obj = [t for n, t in self.env.map['territories'].items() if t['id'] == nid][0]
                            for nn in n_obj['neighbours']:
                                nid2 = [t['id'] for n, t in self.env.map['territories'].items() if t['name'] == nn]
                                if nid2 and self.env.curr_gamestate[nid2[0]][0] != self.player_id:
                                    nde = True
                                    break
                        except Exception:
                            continue
                        if nde:
                            try:
                                self.env.fortify(tid, nid, 1)
                                raise StopIteration
                            except StopIteration:
                                break
                            except Exception:
                                pass
        except Exception:
            pass

        # END TURN
        try:
            self.env.change_turn()
            self.env.give_troops_to_deploy()
        except Exception:
            pass

        return
