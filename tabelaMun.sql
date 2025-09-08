--
-- PostgreSQL database dump
--

-- Dumped from database version 16.1
-- Dumped by pg_dump version 16.1

-- Started on 2025-07-09 13:20:37

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 219 (class 1259 OID 32781)
-- Name: tbufMun; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."tbufMun" (
    "codMun" bigint NOT NULL,
    "nomMun" character varying(80),
    "UF" character(2)
);


ALTER TABLE public."tbufMun" OWNER TO postgres;

--
-- TOC entry 4853 (class 0 OID 32781)
-- Dependencies: 219
-- Data for Name: tbufMun; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1500107, 'Abaetetuba', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1501303, 'Barcarena', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1504604, 'Mocajuba', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1504703, 'Moju', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1503309, 'Igarapé-Miri', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1500206, 'Acará', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1500800, 'Ananindeua', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1500503, 'Almerim', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1501204, 'Baião', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1500859, 'Anapu', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1501402, 'Belém', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1501501, 'Benevides', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1501808, 'Breves', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1502707, 'Conceição do Araguaia', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1502400, 'Castanhal', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1502202, 'Capanema', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1503044, 'Floresta do Araguaia', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1508001, 'Tomé-Açú', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1507904, 'Soure', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1507755, 'Sapucaia', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1507003, 'Santo Antônio do Tauá', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505403, 'Ourém', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505106, 'Óbidos', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505205, 'Oeiras do Pará', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505502, 'Paragominas', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1504901, 'Muaná', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505536, 'Parauapebas', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1506559, 'Santa Luzia do Pará', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1506138, 'Redenção', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1508126, 'Ulianópolis', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1506807, 'Santarém', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1507953, 'Tailândia', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505635, 'Piçarra', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1504422, 'Marituba', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1508100, 'Tucuruí', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1508084, 'Tucumã', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1508308, 'Viseu', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1504208, 'Marabá', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505601, 'Peixe-Boi', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505437, 'Ourilândia do Norte', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505486, 'Pacajá', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505494, 'Palestina do Pará', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505304, 'Oriximiná', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505650, 'Placas', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505700, 'Ponta de Pedras', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505809, 'Portel', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505908, 'Porto de Moz', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1506005, 'Prainha', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1506104, 'Primavera', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1506112, 'Quatipuru', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1506187, 'Rondom do Pará', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1506195, 'Rurópolis', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1506203, 'Salinópolis', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1506302, 'Salvaterra', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (2927903, 'Santa Inês', 'BA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (2109106, 'Presidente Dutra', 'MA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (2925600, 'Presidente Dutra', 'BA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1100205, 'Porto Velho', 'RO');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (2511806, 'Pirpirituba', 'PB');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (2108504, 'Pindaré-Mirim', 'MA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (5106422, 'Peixoto de Azevedo', 'MT');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1716307, ' Pau D-arco', 'TO');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1505551, ' Pau D-arco', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1713205, ' Miracema do Tocantins', 'TO');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1504000, 'Limoeiro do Ajuru', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1302603, 'Manaus', 'AM');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1600808, 'Vitória do Jari', 'AP');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (3550308, 'São Paulo', 'SP');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (2111300, 'São Luís', 'MA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (4125506, 'São José dos Pinhais', 'PR');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1507508, 'São João do Araguaia', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1702109, 'Araguaína', 'TO');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (2101400, 'Balsas', 'MA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1502905, 'Curuçá', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (2105302, 'Imperatriz', 'MA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1503804, 'Jacundá', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1503705, 'Itupiranga', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (3131901, 'Itabirito', 'MG');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (5208707, 'Goiânia', 'GO');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1705508, 'Colinas do Tocantins', 'TO');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (5300108, 'Brasilia', 'DF');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (2102754, 'Capinzal do Norte', 'MA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1703800, 'Buriti do Tocantins', 'TO');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (3106200, 'Belo Horizonte', 'MG');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (2513851, 'Santo André', 'PA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1600600, 'Santana', 'AP');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (2928208, 'Santana', 'BA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (1600303, 'Macapá', 'AP');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (2106904, 'Monção', 'MA');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (5105002, 'Jauru', 'MT');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (3203056, 'Jaguarembé', 'ES');
INSERT INTO public."tbufMun" ("codMun", "nomMun", "UF") VALUES (2203909, 'Floriano', 'PI');


--
-- TOC entry 4709 (class 2606 OID 40984)
-- Name: tbufMun pkcodmun; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."tbufMun"
    ADD CONSTRAINT pkcodmun PRIMARY KEY ("codMun");


-- Completed on 2025-07-09 13:20:37

--
-- PostgreSQL database dump complete
--

