

## Aannames.

Het schema is een [ster model](https://en.wikipedia.org/wiki/Star_schema).

## Stappen plan

1. join alle tabellen bij elkaar tot de IKV tabel
2. pas synthpop toe op die tabel
3. split de tabel terug in de kleinere tabellen.

## Stappen plan voor 2 tabellen. 
Tabel X = [id (pk), X1,X2,X3], tabel Y = [id (fk), Y1, Y2, Y3].

1. Join de tabellen aan elkaar. Resultaat: T = [id,X1,X2,X3,Y1,Y2,Y3]
2. Pas synthpop toe S = [X1,X2,X3,Y1,Y2,Y3]
3. Group by X1,X2,X3, en deel id's daar op uit. Deze id is uniek per X1,X2,X3. Resultaat: A = [id,X1,X2,X3,Y1,Y2,Y3]
4. Xs = select distinct id,X1,X2,X3 from A
Ys = select distinct id,Y1,Y2,Y3 from A

## Stappen plan voor hele schema.
We nemen aan dat er een vaste volgorde in de punten van de ster is.
Het schema is T = [ T_1, T_2,T3,...T_n].

1. Pas Stappen plan voor 2 tabellen toe op T2 en T1. 
stel dat tabellen 1 tot m gesynthetiseerd zijn (S_1 .... S_m).
2. Join T_1 ... T_{m+1}.
3. Pas Stappen plan voor 2 tabellen tot en met het fitten.
4. Join S_1 ...S_m. = A_m
5. gebruik A_m omdata verder te generen in "Stappen plan voor 2 tabellen"
6. Hier komt S_{m+1} uit voort. 
