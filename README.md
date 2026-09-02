# Doomrocket development

[![Repository quality](https://github.com/Ensrick/doomrocket-private/actions/workflows/repository-quality.yml/badge.svg)](https://github.com/Ensrick/doomrocket-private/actions/workflows/repository-quality.yml)

Experimental development repository for the Warprocket Bombardier mod for
Vermintide 2. This repository is public so testers can inspect changes and
submit reproducible bug reports, but its Workshop build is not the public
release line.

- [Current project status](PROJECT_STATUS.md)
- [Development issue chooser](https://github.com/Ensrick/doomrocket-private/issues/new/choose)
- [Two-minute tester quickstart](docs/TESTER_QUICKSTART.md)

The stable public-alpha source is maintained at
[Ensrick/doomrocket-public](https://github.com/Ensrick/doomrocket-public).
The clearly marked development build is
[Workshop item 3794172730](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730);
the public alpha remains
[Workshop item 3771657344](https://steamcommunity.com/sharedfiles/filedetails/?id=3771657344).

Do not enable the public and development Workshop builds at the same time;
they intentionally retain the same in-game mod identity for save and network
compatibility.

## Installation

1. Subscribe to [Vermintide Mod Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=1369573612).
2. Subscribe to [TEST Workshop item 3794172730](https://steamcommunity.com/sharedfiles/filedetails/?id=3794172730).
3. In the launcher, enable both and place Vermintide Mod Framework above
   Warprocket Bombardier.
4. Disable public-alpha item `3771657344` and launch the **Modded Realm**.

For reports, attach the complete matching console log rather than pasting it
into an issue. See [bug-reporting instructions](docs/BUG_REPORTING.md).

## Development documentation

- [Ballistic launcher-aim test protocol](docs/testing/WARLOCK_BALLISTIC_AIM_TEST_PROTOCOL.md)
- [Combat regression protocol](docs/testing/WARLOCK_COMBAT_TEST_PROTOCOL.md)
- [Doomrocket sound test protocol](docs/testing/DOOMROCKET_SOUND_TEST_PROTOCOL.md)
- [Ragdoll runtime test protocol](docs/testing/WARLOCK_RAGDOLL_TEST_PROTOCOL.md)
- [Release-channel and publication procedure](docs/RELEASE_CHANNELS.md)

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). GitHub Actions validates source
contracts, but SDK compilation and in-game behavior remain local/runtime gates.
