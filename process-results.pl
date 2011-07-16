#!/usr/bin/perl

while(<>)
{
    ($pct, $icsd, $csd, $sd, $matched) =
        (m/(\d\d)%, icsd=(-?\d\.\d\d), csd=(-?\d\.\d\d), sd=(-?\d.\d\d) matched avg ([\d\.]+)%/);
    if(defined($matched) && $matched>56)
    {
        print "$pct, icsd=$icsd, csd=$csd, sd=$sd, matched=$matched\n";
    }
}

