CFLAGS = -Wall -O2 -D_GNU_SOURCE -g
LDFLAGS = -lm -g

out: x.o
	gcc -o out $< $(LDFLAGS)

clean:
	rm x.o out
