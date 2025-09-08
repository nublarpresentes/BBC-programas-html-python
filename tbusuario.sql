--
-- PostgreSQL database dump
--

-- Dumped from database version 16.1
-- Dumped by pg_dump version 16.1

-- Started on 2025-07-09 13:51:01

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
-- TOC entry 231 (class 1259 OID 57344)
-- Name: tbusuario; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tbusuario (
    usuario bigint NOT NULL,
    senha character varying(15),
    nivel integer,
    email character varying(150),
    nome character varying(80)
);


ALTER TABLE public.tbusuario OWNER TO postgres;

--
-- TOC entry 4850 (class 0 OID 57344)
-- Dependencies: 231
-- Data for Name: tbusuario; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.tbusuario VALUES (20231844846, '@Sigma4321', 0, 'marco.cordovil2025@gmail.com', NULL);
INSERT INTO public.tbusuario VALUES (15442365220, '@Sigma4321', 1, 'marco.cordovil2025@gmail.com', NULL);
INSERT INTO public.tbusuario VALUES (2335222, '@Sigma4321', 0, 'marco.cordovil@ifpa.edu.br', 'marco cordovil');


--
-- TOC entry 4706 (class 2606 OID 57348)
-- Name: tbusuario pkusuario; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tbusuario
    ADD CONSTRAINT pkusuario PRIMARY KEY (usuario);


-- Completed on 2025-07-09 13:51:01

--
-- PostgreSQL database dump complete
--

