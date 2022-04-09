#include <stdio.h>
#include <math.h>
#include <stdint.h>

#define TILE_RES 256

blah

int lon2tilex(double lon, int z)
{
	return (int)(floor((lon + 180.0) / 360.0 * (1 << z)));
}

int lat2tiley(double lat, int z)
{
	double latrad = lat * M_PI/180.0;
	return (int)(floor((1.0 - asinh(tan(latrad)) / M_PI) / 2.0 * (1 << z)));
}

double tilex2lon(int x, int z)
{
	return x / (double)(1 << z) * 360.0 - 180;
}

double tiley2lat(int y, int z)
{
	double n = M_PI - 2.0 * M_PI * y / (double)(1 << z);
	return 180.0 / M_PI * atan(0.5 * (exp(n) - exp(-n)));
}

int lon2pxx(double lon, int z)
{
	int tilex;
	double basex;
	double tilew;

	tilex = lon2tilex(lon, z);
	basex = tilex2lon(tilex, z);
	tilew = 360.0 / (1 << z);

	return round(fabs(lon - basex) / tilew * TILE_RES);
}

int lat2pxy(double lat, int z)
{
	int tiley;
	double basey;
	double tileh;

	tiley = lat2tiley(lat, z);
	basey = tiley2lat(tiley, z);
	tileh = tiley2lat(tiley, z) - tiley2lat(tiley + 1, z);

	return round(fabs(lat - basey) / tileh * TILE_RES);
}

int main(int argc, char **argv)
{
	double lat, lon, alt;
	int z;

	lat = 53.239135;
	lon = -6.245092;
	alt = 10.0;
	z = 16;

	printf("lat: %f lon: %f alt: %f\n", lat, lon, alt);
	printf("%d/%d/%d.png\n", z, lon2tilex(lon, z), lat2tiley(lat, z));
	printf("%d %d\n", lon2pxx(lon, z), lat2pxy(lat, z));
}
