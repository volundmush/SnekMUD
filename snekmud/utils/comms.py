import re
from typing import Optional
from enum import IntFlag
from mudforge.ansi.circle import CircleToRich


class ActType(IntFlag):
    TO_ROOM = 1
    TO_VICT = 2
    TO_NOTVICT = 3
    TO_CHAR = 4
    TO_GMOTE = 5
    TO_SLEEP = 256
    DG_NO_TRIG = 512
    TO_SNEAKRESIST = 1024
    TO_HIDERESIST = 2048


RE_SUB = re.compile(r"\$(?P<cmd>\$|n|N|m|M|s|S|e|E|o|O|a|A|t|T|F|U)", flags=re.MULTILINE)


async def perform_act(msg: str, actor: "CharacterInstanceDriver" = None, thing: "ItemInstanceDriver" = None,
                      victim: "CharacterInstanceDriver" = None, to: "CharacterInstanceDriver" = None):

    found = dict()
    capitalize_next = False

    def do_sub(match_obj):
        """
        $n = Actor name.
        $N = Victim name.
        $m = actor's objective sex pronoun
        $M = victim's objective sex pronoun
        $s = actor's possessive sex pronoun
        $S = victim's possessive sex pronoun
        $e = actor's objective sex pronoun
        $E = victim's objective sex pronoun
        $o = the "thing" the actor's using (IE: a weapon)'s name
        $O = if the victim is an object, use this to get its name instead of $N
        $p = short description of the actor's thing
        $P = short description of the THING VICTIM
        $a = "an" or "a" depending on the name of the actor's thing
        $A = like $a but for the THING VICTIM
        $T = sets a variable if victim isn't null?
        $t = terminates if obj is null....
        $F = some kind of lookup that gets vict_obj's owner's name
        $u = uppercase previous word. I will not do this- will rewrite anything that uses $u.
        $U = set flag to str.capitalize() the next word.
        $$ = a literal $
        """
        nonlocal capitalize_next
        m = match_obj.group(1)
        out = ""
        match m:
            case "$":
                out = "$"
            case "n":
                if not (out := found.get("actor_name", None)):
                    out = to.get_name_of(actor)
                    found["actor_name"] = out
            case "N":
                if not (out := found.get("victim_name", None)):
                    out = to.get_name_of(victim)
                    found["victim_name"] = out
            case "m":
                if not (out := found.get("actor_objective", None)):
                    out = actor.get_sex().objective()
                    found["actor_objective"] = out
            case "M":
                if not (out := found.get("victim_objective", None)):
                    out = victim.get_sex().objective()
                    found["victim_objective"] = out
            case "s":
                if not (out := found.get("actor_subjective", None)):
                    out = actor.get_sex().subjective()
                    found["actor_subjective"] = out
            case "S":
                if not (out := found.get("victim_subjective", None)):
                    out = victim.get_sex().subjective()
                    found["victim_subjective"] = out
            case "e":
                if not (out := found.get("actor_possessive", None)):
                    out = actor.get_sex().possessive()
                    found["actor_possessive"] = out
            case "E":
                if not (out := found.get("victim_possessive", None)):
                    out = victim.get_sex().possessive()
                    found["victim_possessive"] = out
            case "o":
                out = thing.entity.name
            case "O":
                out = victim.entity.name
            case "a":
                out = "an" if thing.entity.name[0].lower() in "aeiou" else "a"
            case "A":
                out = "an" if victim.entity.name[0].lower() in "aeiou" else "a"
            case "t":
                pass
            case "T":
                pass
            case "F":
                out = "UNIMPLEMENTED"
            case "U":
                capitalize_next = True

        if m != "U" and capitalize_next:
            capitalize_next = False
            return out.capitalize()
        else:
            return out

    out_text = RE_SUB.sub(do_sub, msg)
    await to.msg(line=CircleToRich(out_text), source=actor)


async def act(msg: str, hide_invisible: bool = False, actor: "CharacterInstanceDriver" = None,
              thing: "ItemInstanceDriver" = None, victim: "CharacterInstanceDriver" = None,
              act_type: ActType = ActType.TO_CHAR):
    if not msg:
        return

    to_sleeping = False
    res_sneak = 0
    res_hide = 0
    dcval = 0
    resskill = 0
    to: Optional["CharacterInstanceDriver"] = None

    changed_type = act_type

    if to_sleeping := (changed_type & ActType.TO_SLEEP):
        changed_type &= ~ActType.TO_SLEEP

    if res_sneak := (changed_type & ActType.TO_SNEAKRESIST):
        changed_type &= ~ActType.TO_SNEAKRESIST

    if res_hide := (changed_type & ActType.TO_HIDERESIST):
        changed_type &= ~ActType.TO_HIDERESIST

    # Sneaky stuff here?

    # DG act check?

    if changed_type == ActType.TO_CHAR:
        if not actor:
            return
        return await perform_act(msg=msg, actor=actor, thing=thing, victim=victim, to=actor)

    if changed_type == ActType.TO_VICT:
        if not victim:
            return
        to = victim
        return await perform_act(msg=msg, actor=actor, thing=thing, victim=victim, to=victim)

    # Gmote stuff?

    if changed_type & ActType.TO_ROOM or changed_type & ActType.TO_NOTVICT:
        if not (loc := actor.location):
            return
        if not (inhab := loc.get_other_characters(actor)):
            return
        if changed_type & ActType.TO_NOTVICT:
            if victim in inhab:
                inhab.remove(victim)
        if not inhab:
            return
        for i in inhab:
            await perform_act(msg=msg, actor=actor, thing=thing, victim=victim, to=i)
