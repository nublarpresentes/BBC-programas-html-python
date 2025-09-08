--
-- PostgreSQL database dump
--

-- Dumped from database version 16.1
-- Dumped by pg_dump version 16.1

-- Started on 2025-07-09 13:27:20

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
-- TOC entry 229 (class 1259 OID 41042)
-- Name: tbUF; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."tbUF" (
    uf character(2) NOT NULL,
    estado character varying(50) NOT NULL,
    populacao integer
);


ALTER TABLE public."tbUF" OWNER TO postgres;

--
-- TOC entry 4853 (class 0 OID 41042)
-- Dependencies: 229
-- Data for Name: tbUF; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public."tbUF" VALUES ('PA', 'PARÁ', NULL);
INSERT INTO public."tbUF" VALUES ('AP', 'AMAPÁ', NULL);
INSERT INTO public."tbUF" VALUES ('RO', 'RONDÔNIA', NULL);
INSERT INTO public."tbUF" VALUES ('RR', 'RORAIMA', NULL);
INSERT INTO public."tbUF" VALUES ('AC', 'ACRE', NULL);
INSERT INTO public."tbUF" VALUES ('AM', 'AMAZONAS', NULL);
INSERT INTO public."tbUF" VALUES ('MA', 'MARANHÃO', NULL);
INSERT INTO public."tbUF" VALUES ('RN', 'RIO GRANDE DO NORTE', NULL);
INSERT INTO public."tbUF" VALUES ('RS', 'RIO GRANDE DO SUL', NULL);
INSERT INTO public."tbUF" VALUES ('CE', 'CEARÁ', NULL);
INSERT INTO public."tbUF" VALUES ('PE', 'PERNAMBUCO', NULL);
INSERT INTO public."tbUF" VALUES ('PI', 'PIAUÍ', NULL);
INSERT INTO public."tbUF" VALUES ('PB', 'PARAÍBA', NULL);
INSERT INTO public."tbUF" VALUES ('AL', 'ALAGOAS', NULL);
INSERT INTO public."tbUF" VALUES ('BA', 'BAHIA', NULL);
INSERT INTO public."tbUF" VALUES ('DF', 'DISTRITO FEDERAL', NULL);
INSERT INTO public."tbUF" VALUES ('GO', 'GOIÁS', NULL);
INSERT INTO public."tbUF" VALUES ('MS', 'MATO GROSSO DO SUL', NULL);
INSERT INTO public."tbUF" VALUES ('MG', 'MINAS GERAIS', NULL);
INSERT INTO public."tbUF" VALUES ('TO', 'TOCANTINS', NULL);
INSERT INTO public."tbUF" VALUES ('RJ', 'RIO DE JANEIRO', NULL);
INSERT INTO public."tbUF" VALUES ('SP', 'SÃO PAULO', NULL);
INSERT INTO public."tbUF" VALUES ('ES', 'ESPÍRITO SANTO', NULL);
INSERT INTO public."tbUF" VALUES ('PR', 'PARANÁ', NULL);
INSERT INTO public."tbUF" VALUES ('MT', 'MATO GROSSO', NULL);
INSERT INTO public."tbUF" VALUES ('SE', 'SERGIPE', NULL);
INSERT INTO public."tbUF" VALUES ('SC', 'SANTA CATARINA', NULL);


--
-- TOC entry 4709 (class 2606 OID 41046)
-- Name: tbUF tbUF_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."tbUF"
    ADD CONSTRAINT "tbUF_pkey" PRIMARY KEY (uf);


-- Completed on 2025-07-09 13:27:21

--
-- PostgreSQL database dump complete
--

